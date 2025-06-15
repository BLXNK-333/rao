from typing import Dict, Union

import tkinter as tk
from tkinter import ttk

from ...enums import DispatcherType, EventType
from ...eventbus import EventBus, Subscriber


class TooltipManager:
    def __init__(self, master, delay=500, wraplength=400):
        self.master = master
        self.delay = delay
        self.wraplength = wraplength

        self._tooltip_window = None
        self._after_id = None
        self._last_target = None

        # Один словарь на всё: widget -> tooltip_data (str или dict)
        self._widget_tooltips: Dict[tk.Widget, Union[str, Dict[str, str]]] = {}

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.UI.REGISTER_TOOLTIP, self.register),
        ]
        for event_type, handler in subscriptions:
            EventBus.subscribe(
                event_type=event_type,
                subscriber=Subscriber(
                    callback=handler,
                    route_by=DispatcherType.TK,
                )
            )

    def register(self, widget: tk.Widget, data: Union[str, Dict[str, str]]):
        """Регистрирует tooltip для любого поддерживаемого виджета"""
        if isinstance(widget, (tk.Button, ttk.Button)):
            self.add_widget_tooltip(widget, data)
        elif isinstance(widget, ttk.Treeview):
            self.add_treeview_heading_tooltips(widget, data)

    def add_widget_tooltip(self, widget: tk.Widget, text: str):
        """Добавляет простой tooltip для кнопок и других виджетов"""
        self._widget_tooltips[widget] = text
        widget.bind("<Enter>", self._on_widget_enter)
        widget.bind("<Leave>", self._on_widget_leave)

    def add_treeview_heading_tooltips(self, treeview: ttk.Treeview,
                                      heading_texts: Dict[str, str]):
        """Добавляет tooltip к заголовкам Treeview"""
        self._widget_tooltips[treeview] = heading_texts
        treeview.bind("<Motion>", self._on_treeview_motion)
        treeview.bind("<Leave>", self._on_treeview_leave)

    def _on_widget_enter(self, event):
        widget = event.widget
        text = self._widget_tooltips.get(widget)
        if not text:
            return

        self._cancel_tooltip()
        self._after_id = widget.after(
            self.delay,
            lambda: self._show_tooltip(text, event.x_root + 12, event.y_root + 10)
        )
        self._last_target = widget

    def _on_widget_leave(self, event):
        self._cancel_tooltip()

    def _on_treeview_motion(self, event):
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region != "heading":
            self._cancel_tooltip()
            return

        col_id = tree.identify_column(event.x)
        if not col_id or col_id == self._last_target:
            return

        heading_texts = self._widget_tooltips.get(tree)
        if not isinstance(heading_texts, dict):
            return

        self._cancel_tooltip()

        text = heading_texts.get(col_id)
        if not text:
            heading_info = tree.heading(col_id)
            text = heading_info.get("text", "")

        self._after_id = tree.after(
            self.delay,
            lambda: self._show_tooltip(text, event.x_root + 12, event.y_root + 10)
        )
        self._last_target = col_id

    def _on_treeview_leave(self, event):
        self._cancel_tooltip()

    def _cancel_tooltip(self):
        if self._after_id and self.master:
            self.master.after_cancel(self._after_id)
        self._after_id = None
        self._hide_tooltip()
        self._last_target = None

    def _show_tooltip(self, text, x, y):
        self._hide_tooltip()

        self._tooltip_window = tk.Toplevel(self.master)
        self._tooltip_window.wm_overrideredirect(True)
        self._tooltip_window.wm_geometry(f"+{x}+{y}")

        frame = ttk.Frame(self._tooltip_window, style="Tooltip.TFrame")
        frame.pack()

        label = ttk.Label(
            frame,
            text=text,
            wraplength=self.wraplength,
            style="CustomTooltip.TLabel",
            justify="left"
        )
        label.pack()

    def _hide_tooltip(self):
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None
