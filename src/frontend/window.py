from typing import cast, Optional
import sys
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

from .widgets import BaseWindow, TopMenu, Terminal, CardManager

from ..eventbus import EventBus, Subscriber, Event
from ..enums import TERM, EventType, DispatcherType, STATE


class Window(tk.Tk, BaseWindow):
    def __init__(self, geometry: Optional[dict] = None):
        super().__init__()
        self.withdraw()
        self.title("PAO")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._set_icon()

        # Параметры для сохранения состояния размера окна
        self._last_geometry = (geometry or {}).get("geometry", "800x600")
        self._normal_geometry = (geometry or {}).get("normal_geometry", self._last_geometry)
        self._is_zoomed = (geometry or {}).get("zoomed", False)
        self._resize_after_id = None  # <--- таймер after для дебаунса
        self.bind("<Configure>", self._on_configure)

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

        # Нужен для управления карточками перед закрытием
        self.card_manager: Optional[CardManager] = None

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
        menu.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Настройки размещения для фрейма терминала (2 строка в сетке)
        if self.terminal_visible:
            if self.terminal_state == TERM.LARGE:
                self.hide_frame()
            self.display_terminal()

        # Подписку сделал тут, после всех размещений, иначе подтормаживает
        # переключение размеров терминала.
        self.subscribe()

        if sys.platform == "win32" and self._is_zoomed:
            self.state("zoomed")
        else:
            self.show_centered(geometry=self._last_geometry)

    def _on_configure(self, event):
        if event.widget is not self:
            return

        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)

        self._resize_after_id = self.after(1000, lambda _=None: self._on_resize_debounced())

    def _on_resize_debounced(self):
        self._resize_after_id = None

        current_geometry = self.geometry()
        is_zoomed = self.state() == "zoomed"

        if current_geometry != self._last_geometry or self._is_zoomed != is_zoomed:
            if not is_zoomed:
                self._normal_geometry = current_geometry  # сохранить обычную геометрию

            self._last_geometry = current_geometry
            self._is_zoomed = is_zoomed

            EventBus.publish(
                Event(event_type=EventType.VIEW.UI.WINDOW_RESIZED),
                STATE.WINDOW_GEOMETRY,
                {
                    "geometry": current_geometry,
                    "normal_geometry": self._normal_geometry,
                    "zoomed": is_zoomed
                }
            )

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

        self.destroy()
        EventBus.publish(Event(event_type=EventType.VIEW.UI.CLOSE_WINDOW))

    def close(self):
        self.after(0, lambda _=None: self._on_close())
