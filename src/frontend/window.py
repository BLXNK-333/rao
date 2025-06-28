from typing import cast, Optional, Union, Dict
import sys
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

from .widgets import BaseWindow, TopMenu, Terminal, CardManager

from ..eventbus import EventBus, Subscriber, Event
from ..enums import TERM, EventType, DispatcherType


class Window(tk.Tk, BaseWindow):
    def __init__(
            self,
            geometry: str = "800x600",
            terminal_visible: bool = False,
            terminal_state: Union[TERM, str] = TERM.MEDIUM
    ):
        super().__init__()
        self.withdraw()
        self.title("PAO")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._set_icon()
        self._geometry = geometry
        self.terminal_visible = terminal_visible  # (сначала скрыт)
        self.terminal_state = TERM(terminal_state)      # (начальный размер)

        # Настройки grid
        self.grid_rowconfigure(1, weight=1)  # main area
        self.grid_columnconfigure(0, weight=1)

        # Настройки контейнера для фреймов (1 строка в сетке)
        self.content = ttk.Frame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=0)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.frame_map: Dict[str, ttk.Frame] = {}
        self.current_frame = None
        self.terminal = None                # (установить после через self.setup_layout)

        # Нужен для управления карточками перед закрытием
        self.card_manager: Optional[CardManager] = None
        self.subscribe()

    def subscribe(self):
        handlers = {
            EventType.VIEW.TERM.LARGE: lambda: self.resize_grid(TERM.LARGE),
            EventType.VIEW.TERM.MEDIUM: lambda: self.resize_grid(TERM.MEDIUM),
            EventType.VIEW.TERM.SMALL: lambda: self.resize_grid(TERM.SMALL),
            EventType.VIEW.TERM.CLOSE: self.toggle_terminal,
        }

        for event_type, handler in handlers.items():
            EventBus.subscribe(
                event_type,
                Subscriber(callback=handler, route_by=DispatcherType.TK)
            )

    def setup_layout(self, menu: TopMenu, terminal: Terminal, card_manager: CardManager):
        self.terminal = terminal
        self.card_manager = card_manager

        # Настройки размещения меню фреймов (0 строка в сетке)
        menu.grid(row=0, column=0, sticky="ew")

        # Настройки размещения для фрейма терминала (2 строка в сетке)
        if self.terminal_visible:
            if self.terminal_state == TERM.LARGE:
                self.hide_frame()
            self.display_terminal()

        self.show_centered(geometry=self._geometry)

    def _set_icon(self):
        """
        Sets the application window icon on Windows platforms.
        This function has no effect on non-Windows platforms.
        """
        if sys.platform == "win32":
            if getattr(sys, "frozen", False):
                meipass = cast(str, getattr(sys, "_MEIPASS", ""))
                icon_path = Path(meipass) / "rao.ico"
            else:
                icon_path = Path(__file__).resolve().parents[2] / "rao.ico"

            self.iconbitmap(icon_path)

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

    def _on_close(self):
        if self.card_manager.has_open_cards():
            result = messagebox.askyesno(
                "Уведомление",
                "Некоторые карточки не были сохранены. Выйти без сохранения?",
                parent=self
            )
            if not result:
                self.card_manager.lift_all_cards()
                return  # пользователь отменил закрытие

        self.withdraw()
        self.update()
        self.quit()
        self.after_idle(lambda _=None: self.destroy())

        EventBus.publish(Event(event_type=EventType.VIEW.UI.CLOSE_WINDOW))

    def close(self):
        self.after(0, lambda _=None: self._on_close())
