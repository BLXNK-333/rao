import logging

from .eventbus import EventBus, Event
from .enums import EventType


class ClassNameFilter(logging.Filter):
    """
    Logging filter that adds the final segment of the logger's name
    (typically the module name) to the log record as `class_name`.
    Useful for displaying concise origin information in logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add `class_name` attribute to the log record.

        :param record: The log record being processed.
        :return: Always returns True to allow the record to be logged.
        """
        record.class_name = record.name.split('.')[-1]
        return True


class TkinterTextHandler(logging.Handler):
    """
    Custom logging handler that emits log messages via the event bus.
    Designed for integration with Tkinter UIs by sending logs as events,
    allowing safe inter-thread delivery without explicit queues.
    """

    def __init__(self) -> None:
        """
        Initialize the event-driven log handler.
        """
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a formatted log message as an event.

        :param record: The log record to be emitted.
        """
        msg = self.format(record)
        EventBus.publish(
            Event(event_type=EventType.BACK.LOGGER.EMITTED),
            msg, record.levelname.lower()
        )


def set_logging_config() -> None:
    """
    Set up logging to send formatted messages through the event bus.
    Attaches a custom handler that emits log records as events and
    applies a class name filter for concise source identification.
    """
    log_handler = TkinterTextHandler()

    formatter = logging.Formatter(
        "%(asctime)s - %(class_name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_handler.setFormatter(formatter)
    log_handler.addFilter(ClassNameFilter())

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.DEBUG)
