from functools import partial

from tkinter import ttk
from ttkthemes import ThemedTk

from .widgets import BaseWindow
from .menu import TopMenu
from .terminal import Terminal

from ..eventbus import EventBus, Subscriber, Event
from ..enums import TERM, EventType, DispatcherType


class Window(ThemedTk, BaseWindow):
    def __init__(self):
        super().__init__()
        self.title("RAO")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.close)

        # Настройки grid
        self.grid_rowconfigure(1, weight=1)  # main area
        self.grid_columnconfigure(0, weight=1)

        # Настройки контейнера для фреймов (1 строка в сетке)
        self.content = ttk.Frame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=0)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.current_frame = None
        self.terminal_visible = False       # (сначала скрыт)
        self.terminal_state = TERM.MEDIUM   # (начальный размер)
        self.terminal = None                # (установить после через self.setup_layout)



    def subscribe(self):
        handlers = {
            EventType.VIEW.TERM.LARGE: partial(self.resize_grid, TERM.LARGE),
            EventType.VIEW.TERM.MEDIUM: partial(self.resize_grid, TERM.MEDIUM),
            EventType.VIEW.TERM.SMALL: partial(self.resize_grid, TERM.SMALL),
            EventType.VIEW.TERM.CLOSE: self.toggle_terminal,
        }

        for event_type, handler in handlers.items():
            EventBus.subscribe(
                event_type,
                Subscriber(callback=handler, route_by=DispatcherType.TK)
            )

    def setup_layout(self, menu: TopMenu, terminal: Terminal):
        self.terminal = terminal

        # Настройки размещения меню фреймов (0 строка в сетке)
        menu.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Настройки размещения для фрейма терминала (2 строка в сетке)
        if self.terminal_visible:
            if self.terminal_state == TERM.LARGE:
                self.hide_frame()
            self.display_terminal()

        # Подписку сделал тут, после всех размещений, иначе подтормаживает
        # переключение размеров терминала.
        self.subscribe()
        self.center_window()

    def display_terminal(self):
        self.terminal.grid(row=2, column=0, sticky="nsew")

    def switch_frame(self, target_frame: ttk.Frame):
        if target_frame == self.current_frame:
            return
        if self.current_frame:
            self.current_frame.grid_forget()
        target_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = target_frame

    def resize_grid(self, size: TERM):
        self.terminal_state = size
        if self.terminal_visible:
            if size == TERM.LARGE:
                self.hide_frame()
            else:
                self.show_frame()

    def hide_frame(self):
        self.content.grid_forget()
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

    def show_frame(self):
        self.content.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

    def toggle_terminal(self):
        if self.terminal_visible:
            self.terminal.grid_forget()
            self.show_frame()
        else:
            if self.terminal_state == TERM.LARGE:
                self.hide_frame()
            else:
                self.show_frame()
            self.display_terminal()
        self.terminal_visible = not self.terminal_visible

    def run(self):
        try:
            self.mainloop()
        except Exception:
            import traceback
            traceback.print_exc()
            self.close()

    def close(self):
        self.destroy()
        EventBus.publish(Event(event_type=EventType.VIEW.UI.CLOSE_WINDOW))
