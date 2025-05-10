import tkinter as tk
from tkinter import ttk


def apply_global_bindings(root: tk.Tk):
    """Глобальные бинды: Ctrl+A и авто-снятие выделения при потере фокуса."""

    def on_select_all(event):
        widget = event.widget
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "end")
            widget.see("end")
        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            widget.select_range(0, "end")
            widget.icursor("end")
        return "break"

    def on_focus_out(event):
        widget = event.widget
        try:
            if isinstance(widget, tk.Text):
                widget.tag_remove("sel", "1.0", "end")
            elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
                widget.selection_clear()
        except Exception:
            pass

    def on_button_enter(event):
        try:
            widget = event.widget
            if isinstance(widget, ttk.Button):
                widget.invoke()
        except Exception:
            pass

    # Бинды Ctrl+A
    for cls in ["TEntry", "TCombobox", "Text"]:
        for seq in ("<Control-a>", "<Control-A>"):
            root.bind_class(cls, seq, on_select_all)
        root.bind_class(cls, "<FocusOut>", on_focus_out)

    # Бинды Enter для кнопок
    root.bind_class("TButton", "<Return>", on_button_enter)
    root.bind_class("TButton", "<KP_Enter>", on_button_enter)

