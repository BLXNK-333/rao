from collections.abc import Callable

import tkinter as tk
from tkinter import ttk

from .icons.icon_map import Icons, ICON
from ..eventbus import Subscriber, EventBus
from ..enums import EventType, DispatcherType


class Tab(ttk.Frame):
    def __init__(self, master, text, image=None, command=None):
        super().__init__(master, style="Tab.TFrame")
        self.command = command
        self.text = text
        self.image = image
        self.active = False

        self.label = ttk.Label(
            self,
            text=text,
            image=image,
            compound="left",
            style="Tab.TLabel"
        )
        # Паддинги для label внутри tab
        self.label.pack(fill='both', expand=True, padx=10, pady=5)

        self._bind_all("<Button-1>", self._on_click)
        self._bind_all("<Enter>", self._on_enter)
        self._bind_all("<Leave>", self._on_leave)
        self.set_common()

    def _bind_all(self, event, callback):
        self.bind(event, callback)
        self.label.bind(event, callback)

    def _on_click(self, event):
        if self.command:
            self.command(self)

    def _on_enter(self, event):
        if not self.active:
            # При наведении меняем стиль на "hover"
            self.configure(style="TabHover.TFrame")
            self.label.configure(style="TabHover.TLabel")

    def _on_leave(self, event):
        if not self.active:
            # Убираем hover, возвращаем обычный стиль
            self.configure(style="Tab.TFrame")
            self.label.configure(style="Tab.TLabel")

    def set_active(self):
        self.active = True
        self.configure(style="ActiveTab.TFrame")
        self.label.configure(style="ActiveTab.TLabel")

    def set_common(self):
        self.active = False
        self.configure(style="Tab.TFrame")
        self.label.configure(style="Tab.TLabel")


class MenuBar(ttk.Frame):
    def __init__(self, master, on_tab_selected=None, orient="horizontal", fix_size=True):
        super().__init__(master, style="MenuBar.TFrame", padding=5)
        self.tabs = []
        self.frames = {}
        self.active_tab = None
        self.on_tab_selected = on_tab_selected
        self.fix_size = fix_size

        self.orient = orient
        self.tab_pack_opts = {
            "side": "left" if orient == "horizontal" else "top",
            "padx": 2, "pady": 2
    }

    def add_tab(self, text, frame, image=None):
        tab = Tab(self, text=text, image=image, command=self._on_tab_click)
        tab.pack(**self.tab_pack_opts)
        self.tabs.append(tab)
        self.frames[tab] = frame

        if len(self.tabs) == 1:
            self.set_active(tab)
        if self.fix_size:
            self._synchronize_tab_size()

    def _on_tab_click(self, tab):
        self.set_active(tab)

    def set_active(self, tab):
        if self.active_tab:
            self.active_tab.set_common()

        self.active_tab = tab
        tab.set_active()

        if self.on_tab_selected:
            self.on_tab_selected(self.frames[tab])

    def _synchronize_tab_size(self):
        """Делает все вкладки одинаковыми по размеру."""
        if not self.tabs:
            return

        self.update_idletasks()

        max_width = max(tab.winfo_reqwidth() for tab in self.tabs)
        max_height = max(tab.winfo_reqheight() for tab in self.tabs)

        for tab in self.tabs:
            tab.pack_propagate(False)  # запрет на изменение размера
            tab.configure(width=max_width, height=max_height)


class TermToggler:
    def __init__(
        self,
        parent,
        style: str,
        callback,
        is_visible=False
    ):
        self.is_visible = is_visible
        self.has_active_task = False
        self.callback = callback

        self.icons = Icons()
        self.icon_map = {
            (True, False): self.icons[ICON.TERMINAL_DARK_24],       # Видим, нет задачи
            (True, True):  self.icons[ICON.TERMINAL_DARK_DOT_24],   # Видим, есть задача
            (False, False): self.icons[ICON.TERMINAL_LIGHT_24],       # Скрыт, нет задачи
            (False, True):  self.icons[ICON.TERMINAL_LIGHT_DOT_24],   # Скрыт, есть задача
        }

        self.label = ttk.Label(
            parent,
            image=self._get_icon(),
            style=style
        )
        self.label.pack(side="right", padx=2, pady=2)
        self.label.bind("<Button-1>", self.on_click)

    def _get_icon(self):
        return self.icon_map[(self.is_visible, self.has_active_task)]

    def _refresh(self):
        self.label.configure(image=self._get_icon())

    def on_click(self, event=None):
        self.is_visible = not self.is_visible
        self._refresh()
        self.callback()

    def show(self):
        if not self.is_visible:
            self.is_visible = True
            self._refresh()

    def hide(self):
        if self.is_visible:
            self.is_visible = False
            self._refresh()

    def active(self):
        if not self.has_active_task:
            self.has_active_task = True
            self._refresh()

    def inactive(self):
        if self.has_active_task:
            self.has_active_task = False
            self._refresh()


class TopMenu(MenuBar):
    def __init__(
            self,
            master: tk.Tk,
            on_tab_selected: Callable,
            on_term_selected: Callable,
            term_is_visible: bool = False,
            fix_size: bool = False
    ):
        """
        :param master: The parent container (typically the main application window).
        :param on_tab_selected: Callback function triggered when a tab is selected.
        :param on_term_selected: Callback function triggered when the terminal
            toggle is clicked.
        :param term_is_visible: Whether the terminal is initially visible.
        :param fix_size: Whether the tab menu should use fixed width for tabs.
        """
        super().__init__(master, on_tab_selected=on_tab_selected, fix_size=fix_size)

        # Create terminal toggle label on the right
        self.term_toggler = TermToggler(
            parent=self,
            style="Toggler.TLabel",
            callback=on_term_selected,
            is_visible=term_is_visible
        )

        self.subscribe()


    def subscribe(self):
        for event_type, action in [
            (EventType.BACK.SIG.TASK_RUNNING, self.term_toggler.active),
            (EventType.BACK.SIG.NO_ACTIVE_TASK, self.term_toggler.inactive),
            (EventType.VIEW.TERM.CLOSE, self.term_toggler.hide)
        ]:
            EventBus.subscribe(
                event_type=event_type,
                subscriber=Subscriber(callback=action, route_by=DispatcherType.TK)
            )
