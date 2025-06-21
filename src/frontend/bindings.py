import sys
import tkinter as tk
from tkinter import ttk


def apply_global_bindings(root: tk.Tk):
    """Глобальные бинды: Ctrl+A, Ctrl+V, Ctrl+C, фокус и клавиша Enter на кнопках,
    минорные улучшения."""
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
        root.bind_class(cls, "<Escape>", _on_focus_out)
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


def _on_double_click(event):
    widget = event.widget
    if not isinstance(widget, tk.Text):
        return

    try:
        index = widget.index(f"@{event.x},{event.y}")
        line, col = map(int, index.split('.'))
        line_text = widget.get(f"{line}.0", f"{line}.end").rstrip()

        if not _is_click_inside_text(widget, event) or col >= len(line_text):
            widget.after(1, lambda _=None: _select_last_word_in_line(widget, line_text, line))
        else:
            widget.after(1, lambda _=None: _move_insert_to_sel_end(widget))
    except Exception:
        pass


def _on_triple_click(event):
    widget = event.widget
    if not isinstance(widget, tk.Text):
        return "break"

    try:
        index = widget.index(f"@{event.x},{event.y}")
        line = index.split('.')[0]
        text = widget.get(f"{line}.0", f"{line}.end").rstrip()
        end = f"{line}.{len(text)}"

        widget.tag_remove("sel", "1.0", "end")
        widget.tag_add("sel", f"{line}.0", end)
        widget.mark_set("insert", end)
        widget.see(end)
    except Exception:
        pass

    return "break"


def _move_insert_to_sel_end(widget):
    try:
        if isinstance(widget, tk.Text):
            sel_end = widget.index("sel.last")
            widget.mark_set("insert", sel_end)
            widget.see("insert")

        elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            sel_end = widget.index("sel.last")
            widget.icursor(sel_end)

    except tk.TclError:
        pass


def _on_click(event):
    widget = event.widget
    if not _is_click_inside_text(widget, event):
        # Клик по краю — отложенная установка курсора
        widget.after(1, lambda: _set_cursor_to_end(widget))
    return None


def _set_cursor_to_end(widget: tk.Text):
    widget.mark_set("insert", "end-1c")
    widget.see("insert")


def _is_click_inside_text(widget: tk.Text, event: tk.Event) -> bool:
    try:
        index = widget.index(f"@{event.x},{event.y}")
        bbox = widget.bbox(index)
        if not bbox:
            return False  # Клик вне текста
        x0, y0, w, h = bbox
        return x0 <= event.x <= x0 + w and y0 <= event.y <= y0 + h
    except Exception:
        return False


def _select_last_word_in_line(widget: tk.Text, line_text: str, line: int):
    try:
        if not line_text.strip():
            return
        words = line_text.split()
        if not words:
            return

        last = words[-1]
        start_offset = line_text.rfind(last)
        start = f"{line}.{start_offset}"
        end = f"{line}.{start_offset + len(last)}"

        widget.tag_remove("sel", "1.0", "end")
        widget.tag_add("sel", start, end)
        widget.mark_set("insert", end)
        widget.see(end)
    except Exception:
        pass


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
            if event.keycode == 65:  # Ctrl+A
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


class ContextMenuMixin(tk.Widget):
    """
    Mixin to add a context menu and enhanced selection behavior
    to Tkinter widgets.

    Features:
    - Automatically sets up a context menu with basic commands:
      Cut, Copy, Paste, Select All.
    - Clears selection in text and entry widgets on focus loss.
    - Supports correct cursor positioning on double-click in text widgets (tk.Text).
    - Handles right-click and Ctrl+click to show the context menu.

    Usage:
        class MyText(tk.Text, ContextMenuMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.enable_context_menu()

    The enable_context_menu() method must be called to activate
    the mixin functionality.
    """

    def enable_context_menu(self):
        self._suppress_focus_out = False
        self.bind("<FocusOut>", self._on_focus_out)

        if isinstance(self, tk.Text):
            self.bind("<Button-1>", _on_click)
            self.bind("<Double-Button-1>", _on_double_click, add="+")
            self.bind("<Triple-Button-1>", _on_triple_click, add="+")

        self._add_context_menu()

    def _on_focus_out(self, event):
        def check_focus():
            if getattr(self, "_suppress_focus_out", False):
                return

            try:
                focused = self.focus_get()
                if focused == self:
                    return
                if isinstance(self, tk.Text):
                    self.tag_remove("sel", "1.0", "end")
                elif isinstance(self, (tk.Entry, ttk.Entry, ttk.Combobox)):
                    self.selection_clear()
            except Exception:
                pass

        self.after(100, lambda _=None: check_focus())
        return "break"

    def _add_context_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.configure(
            activeborderwidth=0,
            bd=1,
            font=("Helvetica", 11),
            activeforeground="#222333",
            activebackground="#c9c9c9",
        )

        def select_all():
            event = tk.Event()
            event.widget = self
            _on_select_all(event)

        menu.add_command(label="Вырезать", command=lambda: self.event_generate("<<Cut>>"))
        menu.add_command(label="Копировать",
                         command=lambda: self.event_generate("<<Copy>>"))
        menu.add_command(label="Вставить",
                         command=lambda: self.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Выделить всё", command=select_all)

        def show_menu(event):
            self._suppress_focus_out = True
            self.focus_set()
            menu.tk_popup(event.x_root, event.y_root)
            self.after(200, lambda _=None: setattr(self, "_suppress_focus_out", False))

        self.bind("<Button-3>", show_menu)
        self.bind("<Control-Button-1>", show_menu)
