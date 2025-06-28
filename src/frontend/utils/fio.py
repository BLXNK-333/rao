import tkinter as tk
from tkinter import ttk


class FioInserter:
    """
    Handles transformation of full name from clipboard
    and insertion into a widget with optional prefix ", ",
    preserving the original clipboard content.

    Methods:
        - insert_lfm(): expects format 'Фамилия Имя Отчество'
        - insert_ifl(): expects format 'Имя Отчество Фамилия'
    """

    def __init__(self, widget: tk.Widget):
        self.widget = widget

    def insert_lfm(self):
        self._insert_with(self._transform_fio_lfm)

    def insert_ifl(self):
        self._insert_with(self._transform_fio_ifl)

    def _insert_with(self, transform_func):
        try:
            original = self.widget.clipboard_get().strip()
            transformed = transform_func(original)
            if not transformed:
                return

            if self._should_prepend_comma():
                transformed = ', ' + transformed

            self.widget.clipboard_clear()
            self.widget.clipboard_append(transformed)
            self.widget.update_idletasks()
            self.widget.event_generate("<<Paste>>")

            self.widget.after(50, lambda _=None: self._restore_clipboard(original))
        except Exception:
            pass

    def _should_prepend_comma(self) -> bool:
        try:
            w = self.widget
            if isinstance(w, (tk.Entry, ttk.Entry)):
                text = w.get()
                pos = w.index(tk.INSERT)
                return pos == len(text) and text and not text.rstrip().endswith(',')
            elif isinstance(w, tk.Text):
                if w.index(tk.INSERT) == w.index("end-1c"):
                    text = w.get("1.0", "end-1c").rstrip()
                    return text and not text.endswith(',')
        except Exception:
            return False
        return False

    def _restore_clipboard(self, original: str):
        try:
            self.widget.clipboard_clear()
            self.widget.clipboard_append(original)
        except Exception:
            pass

    @staticmethod
    def _transform_fio_lfm(full_name: str) -> str:
        """
        Преобразует 'Фамилия Имя Отчество' в 'Фамилия И.О.'
        """
        parts = full_name.split()
        if len(parts) != 3:
            return ''
        last, first, middle = parts
        return f'{last.capitalize()} {first[0].upper()}.{middle[0].upper()}.'

    @staticmethod
    def _transform_fio_ifl(full_name: str) -> str:
        """
        Преобразует 'Имя Отчество Фамилия' в 'Фамилия И.О.'
        """
        parts = full_name.split()
        if len(parts) != 3:
            return ''
        first, middle, last = parts
        return f'{last.capitalize()} {first[0].upper()}.{middle[0].upper()}.'
