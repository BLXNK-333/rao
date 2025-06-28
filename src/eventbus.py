import logging
import threading
import queue
from typing import Callable, Dict, List, Optional, Union
from collections import defaultdict
from abc import ABC, abstractmethod

from tkinter import Tk

from .enums import EventType, DispatcherType, GROUP


class Event:
    def __init__(
            self,
            event_type: Union[str, EventType],
            group_id: Optional[GROUP] = None,
    ):
        self.event_type = event_type
        self.group_id = group_id


# Dispatcher interface
class Dispatcher(ABC):
    """Base class for event dispatchers."""

    @abstractmethod
    def dispatch(self, callback: Callable, *args, **kwargs):
        """Execute the callback with given arguments."""
        raise NotImplementedError

    def stop(self):
        """Gracefully stop the dispatcher (if applicable)."""
        pass


class TkDispatcher(Dispatcher):
    """Dispatcher for routing callbacks via Tkinter event loop."""

    def __init__(self, tk: Tk):
        self.tk = tk

    def dispatch(self, callback: Callable, *args, **kwargs):
        """Schedule callback execution in Tkinter's main loop."""
        self.tk.after(0, lambda _=None: callback(*args, **kwargs))


class QueueDispatcher(Dispatcher):
    """Dispatcher with internal queue and daemon thread. Ensures graceful stop."""

    def __init__(self):
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def dispatch(self, callback: Callable, *args, **kwargs):
        """Enqueue the callback for execution in a background thread."""
        self._queue.put(lambda: callback(*args, **kwargs))

    def _worker(self):
        while not self._stop_event.is_set():
            task = self._queue.get()
            if task is None:
                break
            try:
                task()
            finally:
                self._queue.task_done()

    def stop(self):
        """Stop dispatcher gracefully after completing pending tasks."""
        self._stop_event.set()
        self._queue.put(None)
        self._thread.join()


class Subscriber:
    """
    Event subscriber with an optional dispatcher type.

    If dispatcher_type is set, the callback is routed through the corresponding
    dispatcher (e.g. Tk, thread queue). If None, DEFAULT is used.
    """

    def __init__(
            self,
            callback: Callable,
            route_by: DispatcherType,
            group_id: Optional[GROUP] = None
    ):
        self.callback = callback
        self.route_by = route_by
        self.group_id = group_id


class EventBus:
    """
    Central event bus for publishing events and dispatching callbacks.

    Scheme:

        [Producer Threads]
           |
           |  -> EventBus.publish(event, *args, **kwargs)
           v
    +-------------------------+
    |      EventBus (Thread)  |
    |  - internal queue       |
    |  - worker loop          |
    +-------------------------+
           |
           v
    +-------------- dispatch ------------+
    |                 |                  |
    v                 v                  v
    [TKDispatcher] [QueueDispatcher] [QueueDispatcher]
     (UI thread)    (worker thread)   (worker thread)
     (tk.after)     (queue & loop)    (queue & loop)
    """

    _subscribers: Dict[Union[str, EventType], List[Subscriber]] = defaultdict(list)
    _dispatchers: Dict[DispatcherType, Dispatcher] = {}
    _event_queue = queue.Queue()
    _lock = threading.RLock()
    _stop_event = threading.Event()
    _thread: Optional[threading.Thread] = None
    _started = False
    _logger = logging.getLogger(__name__)

    @classmethod
    def start(cls):
        """Start the event worker thread if not already running."""
        with cls._lock:
            if not cls._started:
                cls._thread = threading.Thread(target=cls._worker, daemon=True)
                cls._thread.start()
                cls._started = True

    @classmethod
    def register_dispatcher(cls, dispatcher_type: DispatcherType, dispatcher: Dispatcher):
        """Register a dispatcher to handle callbacks of a given type."""
        with cls._lock:
            cls._dispatchers[dispatcher_type] = dispatcher

    @classmethod
    def subscribe(cls, event_type: Union[str, EventType], subscriber: Subscriber):
        """Subscribe a callback to an event."""
        with cls._lock:
            cls._subscribers[event_type].append(subscriber)

    @classmethod
    def unsubscribe(cls, event_type: Union[str, EventType], subscriber: Subscriber):
        """Unsubscribe a callback from an event."""
        with cls._lock:
            if subscriber in cls._subscribers.get(event_type, []):
                cls._subscribers[event_type].remove(subscriber)

    @classmethod
    def publish(cls, event: Event, *args, **kwargs):
        """Publish an event with optional arguments to all subscribers."""
        cls._event_queue.put((event, args, kwargs))

    @classmethod
    def _worker(cls):
        """Internal worker loop that processes the event queue."""
        while not cls._stop_event.is_set():
            task = cls._event_queue.get()
            if task is None:
                break
            event, args, kwargs = task
            for subscriber in cls._subscribers.get(event.event_type, []):
                # 💡 Событие доставляется только подписчикам, у которых
                # `subscriber.group_id` совпадает с `event.group_id`.
                # Если `event.group_id is None`, оно считается **общим** и доставляется
                # только подписчикам без группы (`subscriber.group_id is None`).
                if subscriber.group_id is not None and subscriber.group_id != event.group_id:
                    continue

                dispatcher = cls._dispatchers.get(subscriber.route_by)

                if dispatcher:
                    dispatcher.dispatch(subscriber.callback, *args, **kwargs)
                else:
                    cls._logger.warning(
                        f"Dispatcher not registered for type: {subscriber.route_by}"
                    )
            cls._event_queue.task_done()

    @classmethod
    def stop_all_dispatchers(cls):
        """Stop the event thread and all registered dispatchers."""
        with cls._lock:
            cls._stop_event.set()
            cls._event_queue.put(None)

            if cls._thread:
                cls._thread.join()
                cls._started = False

            for dispatcher in cls._dispatchers.values():
                dispatcher.stop()

    @classmethod
    def render_subscriber_map(cls) -> str:
        """Render a table of all current subscribers for debugging."""
        with cls._lock:
            sep_len = 150
            lines = []
            header = f"{'EVENT':<30} | CALLBACK"
            lines.append(header)
            lines.append("=" * sep_len)

            for event, subscribers in sorted(cls._subscribers.items()):
                event_str = str(event)
                first = True

                for sub in subscribers:
                    callback_str = repr(sub.callback)
                    if first:
                        lines.append(f"{event_str:<30} | {callback_str}")
                        first = False
                    else:
                        lines.append(f"{'':<30} | {callback_str}")

                lines.append("-" * sep_len)

            return "\n".join(lines)
