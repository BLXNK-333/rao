from functools import partial

from tkinter import ttk
from ttkthemes import ThemedTk

from .widgets import BaseWindow
from .menu import TopMenu
from .terminal import Terminal
from .report import Report
from .export import Export
from .settings import Settings
from .style import UIStyles
from .icons.icon_map import Icons, ICON
from .bindings import apply_global_bindings
from .table.table import Table
from .table.card import CardManager

from ..eventbus import EventBus, Subscriber, Event
from ..enums import TERM, EventType, DispatcherType, GROUP


class ViewUI(ThemedTk, BaseWindow):
    def __init__(self):
        super().__init__()
        self.title("RAO")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.close)

        UIStyles()
        apply_global_bindings(self)
        self.icons = Icons()

        # Настройки grid
        self.grid_rowconfigure(1, weight=1)  # main area
        self.grid_columnconfigure(0, weight=1)

        # Контейнер для фреймов (1 строка в сетке)
        self.content = ttk.Frame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=0)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Основные фреймы (все фреймы в 1 строке сетки)
        self.songs = Table(parent=self.content, group_id=GROUP.SONG_TABLE)
        self.report = Report(parent=self.content)
        self.export = Export(parent=self.content)
        self.settings = Settings(parent=self.content)

        self.card_manager = CardManager(self.content)

        # Устанавливаем текущий фрейм
        self.current_frame = self.songs
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        # Терминал (2 строка в сетке)
        self.terminal_visible = False       # (сначала скрыт)
        self.terminal_state = TERM.MEDIUM   # (начальный размер)
        self.terminal = Terminal(master=self)

        # Верхняя панель (0 строка в сетке)
        self.menu = TopMenu(
            master=self,
            on_tab_selected=self.switch_frame,
            on_term_selected=self.toggle_terminal,
            term_is_visible=self.terminal_visible,
            fix_size=False
        )
        self.add_tabs_in_menu()

        # Размещение
        if self.terminal_visible:
            if self.terminal_state == TERM.LARGE:
                self.hide_frame()
            self.display_terminal()

        self.subscribe()
        self.center_window()

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

    def add_tabs_in_menu(self):
        """Добавляем обычные вкладки"""
        self.menu.add_tab("Songs", self.songs, image=self.icons[ICON.SONGS_LIST_24])
        self.menu.add_tab("Report", self.report, image=self.icons[ICON.REPORT_LIST_24])
        self.menu.add_tab("Export", self.export, image=self.icons[ICON.EXPORT_24])
        self.menu.add_tab("Settings", self.settings, image=self.icons[ICON.SETTINGS_24])

    def display_terminal(self):
        self.terminal.grid(row=2, column=0, sticky="nsew")

    def switch_frame(self, target_frame: ttk.Frame):
        if target_frame == self.current_frame:
            return
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
        self.content.grid(row=1, column=0, sticky="nsew")
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
