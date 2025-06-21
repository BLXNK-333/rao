from typing import Optional, Tuple, Union

from queue import Queue, Empty
import tkinter as tk
from tkinter import ttk

from .widgets import HoverButton
from ..icons import Icons
from ...eventbus import Subscriber, EventBus, Event
from ...enums import TERM, EventType, DispatcherType, ICON


class Terminal(ttk.Frame):
    def __init__(self, master: tk.Tk, state: TERM, msg_queue: Queue) -> None:
        """
        Initialize the Terminal widget and its internal components.

        :param master: The parent window, typically an instance of ViewUI.
        """
        super().__init__(master)
        # UI components
        self.term_panel = TermPanel(self)
        self.term_logger = TermLogger(self)
        self._setup_options(state, msg_queue)

    def _setup_options(self, state: TERM, msg_queue: Queue):
        self.term_panel.set_active_state(state)
        self.term_logger.set_state(state)
        self.term_logger.set_msq_queue(msg_queue)
        self.term_panel.create_widget()
        self.term_logger.create_widget()


class TermPanel(ttk.Frame):
    widget_color = "#dbdbdb"

    def __init__(self, parent: ttk.Frame):
        super().__init__(parent, style="TermPanel.TFrame")
        self.pack(fill="x")
        self.icons = Icons()
        self.buttons = {}
        self.active_state = TERM.MEDIUM

        self.subscribe()

    def subscribe(self):
        for event_type, action in [
            (EventType.BACK.SIG.TASK_RUNNING, self.toggle_red_stop_button),
            (EventType.BACK.SIG.NO_ACTIVE_TASK, self.toggle_gray_stop_button)
        ]:
            EventBus.subscribe(
                event_type=event_type,
                subscriber=Subscriber(callback=action, route_by=DispatcherType.TK)
            )

    def set_active_state(self, state: TERM):
        self.active_state = state

    def create_widget(self) -> None:
        """Создаёт заголовок и кнопки управления."""
        label = ttk.Label(self, text="Терминал", style="TermPanel.TLabel")
        label.pack(side="left", padx=10)

        # Кнопки управления
        icons_map = [
            ("CLOSE", ICON.CLOSE_16, self.on_close_clicked),
            ("LARGE", ICON.TERM_LARGE_LIGHT_16, self.on_large_clicked),
            ("MEDIUM", ICON.TERM_MEDIUM_DARK_16, self.on_medium_clicked),
            ("SMALL", ICON.TERM_SMALL_LIGHT_16, self.on_small_clicked),
            ("CLEAR", ICON.CLEAR_16, self.on_clear_clicked),
            ("STOP", ICON.STOP_GRAY_16, self.on_stop_clicked)
        ]
        for key, icon, command in icons_map:
            btn = HoverButton(
                self,
                image=self.icons[icon], command=command,
                background=self.widget_color,
                activebackground="#c9c9c9"
            )
            btn.pack(side="right", padx=5, pady=3)
            self.buttons[key] = btn

        self._update_size_icons(active_state=self.active_state)

    # region STOP BUTTONS

    def toggle_red_stop_button(self):
        self._set_stop_icon(ICON.STOP_RED_16)

    def toggle_gray_stop_button(self):
        self._set_stop_icon(ICON.STOP_GRAY_16)

    def _set_stop_icon(self, icon_key: ICON):
        btn = self.buttons["STOP"]
        new_icon = self.icons[icon_key]
        if str(btn.cget("image")) != str(new_icon):
            btn.config(image=new_icon)

    # endregion

    # region CLICK HANDLERS

    def on_clear_clicked(self):
        self.focus_set()
        EventBus.publish(Event(event_type=EventType.VIEW.TERM.CLEAR))

    def on_close_clicked(self):
        self.focus_set()
        EventBus.publish(Event(event_type=EventType.VIEW.TERM.CLOSE))

    def on_stop_clicked(self):
        self.focus_set()
        EventBus.publish(Event(event_type=EventType.VIEW.TERM.STOP))

    def on_small_clicked(self):
        self._set_active_state(state=TERM.SMALL, event_type=EventType.VIEW.TERM.SMALL)

    def on_medium_clicked(self):
        self._set_active_state(state=TERM.MEDIUM, event_type=EventType.VIEW.TERM.MEDIUM)

    def on_large_clicked(self):
        self._set_active_state(state=TERM.LARGE, event_type=EventType.VIEW.TERM.LARGE)

    # endregion

    # region SIZE ICON LOGIC

    def _set_active_state(self, state: TERM, event_type: Union[str, EventType]):
        self.focus_set()
        if self.active_state == state:
            return

        self._update_size_icons(state)
        self.active_state = state
        EventBus.publish(Event(event_type=event_type))

    def _update_size_icons(self, active_state: TERM):
        for key in [TERM.SMALL, TERM.MEDIUM, TERM.LARGE]:
            icon_attr = f"TERM_{key.value}_{'DARK' if key == active_state else 'LIGHT'}_16"
            self.buttons[key].config(image=self.icons[getattr(ICON, icon_attr)])

    # endregion


class TermLogger(ttk.Frame):
    # Размеры терминала (в строках)
    HEIGHTS = {
        TERM.SMALL: 5,
        TERM.MEDIUM: 16,
        TERM.LARGE: 0   # Задумано, что будет занимать все доступное пространство.
    }

    TAG_COLORS = {
        "debug": "#868686",     # Gray
        "info": "#DDDDDD",      # White
        "warning": "#E6B800",   # Amber Yellow
        "error": "#FF5858",     # Soft Red
        "critical": "#C62828"   # Deep Red
    }

    BACKGROUND = "#1a1a1a"
    FOREGROUND = "white"
    SELECTBACKGROUND = "#37414F"

    def __init__(self, parent: ttk.Frame):
        super().__init__(parent)
        self.pack(expand=True, fill="both")

        self.active_state: TERM = TERM.MEDIUM
        self.msq_queue: Optional[Queue[Tuple[str, str]]] = None
        self.text: Optional[tk.Text] = None

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.TERM.CLEAR, self._clear_text),
            (EventType.VIEW.TERM.SMALL,
             lambda: self._set_height(self.HEIGHTS[TERM.SMALL])),
            (EventType.VIEW.TERM.MEDIUM,
             lambda: self._set_height(self.HEIGHTS[TERM.MEDIUM])),
            (EventType.VIEW.TERM.LARGE,
             lambda: self._set_height(self.HEIGHTS[TERM.LARGE])),
        ]

        for event_type, callback in subscriptions:
            EventBus.subscribe(
                event_type=event_type,
                subscriber=Subscriber(callback=callback, route_by=DispatcherType.TK)
            )

    def create_widget(self):
        self.text = tk.Text(
            self,
            height=self.HEIGHTS[self.active_state],
            bg=self.BACKGROUND,
            fg=self.FOREGROUND,
            bd=0,
            selectbackground=self.SELECTBACKGROUND,  # Цвет фона выделения
            highlightthickness=1,
            highlightbackground="#555555",  # цвет рамки (неактивной)
            highlightcolor="#555555",
            padx = 5,  # горизонтальный отступ текста
            pady = 5  # вертикальный отступ текста
        )
        self.text.pack(expand=True, fill="both")
        self.text.configure(state="disabled")
        self._configure_log_tags()

        # Start periodic log updates
        self.after(50, lambda _=None: self._update_log())

    def _clear_text(self):
        self.text.config(state="normal")  # Разрешаем редактирование
        self.text.delete("1.0", tk.END)  # Удаляем всё содержимое
        self.text.config(state="disabled")  # Снова блокируем редактирование

    def _set_height(self, size: int):
        """Update the text widget height depending on size setting."""
        if not self.text:
            return
        self.text.config(height=size)

    def _configure_log_tags(self):
        """Configure color tags for different log levels in a Text widget."""
        if self.text is None:
            return

        for tag, color in self.TAG_COLORS.items():
            self.text.tag_configure(tag, foreground=color)

    def set_state(self, state: TERM):
        self.active_state = state

    def set_msq_queue(self, msq_queue: Queue) -> None:
        """
        Sets the message queue for logging.

        :param msq_queue: The queue that receives log messages.
        """
        if self.msq_queue:
            return
        self.msq_queue = msq_queue

    def _update_log(self) -> None:
        """Periodically update the Text widget by extracting logs from the queue."""
        try:
            while not self.msq_queue.empty():
                msg, log_level = self.msq_queue.get_nowait()
                self._write(msg, log_level)
        except Empty:
            pass

        # Schedule the next log update
        self.after(50, lambda _=None: self._update_log())

    def _write(self, msg: str, log_level: str) -> None:
        """
        Insert a log message into the Text widget and scroll to the latest entry.

        :param msg: The formatted log message.
        :param log_level: The log level (e.g., "debug", "info", "error").
        """
        if self.text is None:
            return

        self.text.config(state="normal")
        self.text.insert("end", msg + "\n", log_level)
        self.text.config(state="disabled")
        self.text.see("end")  # Scroll to the bottom
