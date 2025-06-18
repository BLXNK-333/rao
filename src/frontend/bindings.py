import sys
import tkinter as tk
from tkinter import ttk


def apply_global_bindings(root: tk.Tk):
    """Глобальные бинды: Ctrl+A, Ctrl+V, Ctrl+C, фокус и клавиша Enter на кнопках."""
    if sys.platform == "win32":
        _setup_on_windows(root)
    else:
        _setup_on_linux(root)

    _setup_common_bindings(root)


def _setup_common_bindings(root: tk.Tk):
    def on_button_enter(event):
        try:
            widget = event.widget
            if isinstance(widget, ttk.Button):
                widget.invoke()
        except Exception:
            pass

    for cls in ["TEntry", "TCombobox", "Text"]:
        root.bind_class(cls, "<FocusOut>", _on_focus_out)
    root.bind_class("TButton", "<Return>", on_button_enter)
    root.bind_class("TButton", "<KP_Enter>", on_button_enter)


def _on_focus_out(event):
    widget = event.widget
    try:
        if isinstance(widget, tk.Text):
            widget.tag_remove("sel", "1.0", "end")
        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            widget.selection_clear()
    except Exception:
        pass


def _on_select_all(event):
    widget = event.widget
    try:
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "end-1c")
            widget.see("end-1c")
        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            widget.select_range(0, "end")
            widget.icursor("end")
    except Exception:
        pass
    return "break"


def _on_copy(event, root):
    widget = event.widget
    try:
        if isinstance(widget, tk.Text):
            text = widget.get("sel.first", "sel.last")
        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            text = widget.selection_get()
        else:
            return "break"
        root.clipboard_clear()
        root.clipboard_append(text)
    except Exception:
        pass
    return "break"


def _on_paste(event, root):
    widget = event.widget
    try:
        text = root.clipboard_get()
    except Exception:
        return "break"

    try:
        if isinstance(widget, tk.Text):
            try:
                widget.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            widget.insert("insert", text)
            widget.see("insert")

        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            try:
                sel_start = widget.index("sel.first")
                sel_end = widget.index("sel.last")
                widget.delete(sel_start, sel_end)
            except tk.TclError:
                pass

            pos = widget.index("insert")
            widget.insert(pos, text)
            widget.icursor(pos + len(text))

    except Exception:
        pass

    return "break"


def _on_cut(event, root):
    widget = event.widget
    try:
        if isinstance(widget, tk.Text):
            text = widget.get("sel.first", "sel.last")
            widget.delete("sel.first", "sel.last")
        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            text = widget.selection_get()
            sel_start = widget.index("sel.first")
            sel_end = widget.index("sel.last")
            widget.delete(sel_start, sel_end)
        else:
            return "break"
        root.clipboard_clear()
        root.clipboard_append(text)
    except Exception:
        pass
    return "break"


def _setup_on_linux(root: tk.Tk):
    # Тестировал на:
    # OS: Fedora Linux 42 (Workstation Edition) x86_64 , DE: GNOME 48.2, Display: x11
    for cls in ["TEntry", "TCombobox", "Text"]:
        root.bind_class(cls, "<Control-a>", _on_select_all)
        root.bind_class(cls, "<Control-A>", _on_select_all)
        root.bind_class(cls, "<Control-c>", lambda e: _on_copy(e, root))
        root.bind_class(cls, "<Control-C>", lambda e: _on_copy(e, root))
        root.bind_class(cls, "<Control-v>", lambda e: _on_paste(e, root))
        root.bind_class(cls, "<Control-V>", lambda e: _on_paste(e, root))
        root.bind_class(cls, "<Control-x>", lambda e: _on_cut(e, root))
        root.bind_class(cls, "<Control-X>", lambda e: _on_cut(e, root))


def _setup_on_windows(root: tk.Tk):
    # Тестировал на:
    # OS: Windows 7 x64 SP1
    def on_ctrl(event):
        ctrl = (event.state & 0x0004) != 0 or (event.state & 0x0008) != 0
        if ctrl:
            if event.keycode == 65:   # Ctrl+A
                return _on_select_all(event)
            elif event.keycode == 67:  # Ctrl+C
                return _on_copy(event, root)
            elif event.keycode == 86:  # Ctrl+V
                return _on_paste(event, root)
            elif event.keycode == 88:  # Ctrl+X
                return _on_cut(event, root)

        return None

    for cls in ["TEntry", "TCombobox", "Text"]:
        for seq in (
                "<Control-KeyPress>",
                "<Control-a>", "<Control-A>",
                "<Control-c>", "<Control-C>",
                "<Control-v>", "<Control-V>",
                "<Control-x>", "<Control-X>"
        ):
            root.bind_class(cls, seq, on_ctrl)