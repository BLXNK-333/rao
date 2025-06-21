from abc import ABC, abstractmethod

from typing import Dict, Any, List, Union, Tuple
from tkinter import ttk, StringVar, BooleanVar

from ..widgets import ScrolledFrame
from ..icons import Icons
from ...enums import ConfigKey, EventType, TERM, ICON
from ...eventbus import EventBus, Event


class BaseFrame(ttk.Frame, ABC):
    def __init__(self, parent, key: ConfigKey, attr_name: str):
        super().__init__(parent)
        self.key = key
        self.var = None
        # Используем grid для внутренней раскладки
        self.columnconfigure(0, minsize=300)  # примерно ширина для лейбла (примерно 40 символов)
        self.columnconfigure(1, weight=0)  # виджет (чекбокс/комбобокс)
        self.columnconfigure(2, weight=1)  # пустое пространство, растягиваемое вправо

        label = ttk.Label(self, text=attr_name, anchor="w")
        label.grid(row=0, column=0, sticky="w", padx=(5, 10), pady=2)

    def _bind_trace(self):
        if self.var is not None:
            self.var.trace_add("write", self._on_var_changed)

    def _on_var_changed(self, *_):
        EventBus.publish(Event(
            EventType.VIEW.SETTINGS.ON_CHANGE
        ), {self.key: self._get_value()}
        )

    @abstractmethod
    def _get_value(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_value()")

    def add_widget(self, widget: ttk.Widget):
        # Добавить виджет в колонку 1 с отступами
        widget.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=4)


class CheckboxFrame(BaseFrame):
    def __init__(self, parent, key: ConfigKey, value: bool, attr_name: str):
        super().__init__(parent, key, attr_name)
        self.var = BooleanVar(value=bool(value))
        self._bind_trace()
        cb = ttk.Checkbutton(self, variable=self.var)
        self.add_widget(cb)

    def _get_value(self, *_):
        return self.var.get()


class ComboboxFrame(BaseFrame):
    def __init__(self, parent, key: ConfigKey, value: Any, attr_name: str,
                 listbox_options: Dict[str, Any]):
        super().__init__(parent, key, attr_name)
        self.keys_map = listbox_options

        # найти ключ, соответствующий значению
        reverse_map = {v: k for k, v in listbox_options.items()}
        # если не найдено — взять первый
        selected_key = reverse_map.get(value, next(iter(listbox_options)))

        self.var = StringVar(value=selected_key)
        self._bind_trace()

        combo = ttk.Combobox(self, textvariable=self.var,
                             values=list(listbox_options.keys()), state="readonly")
        self.add_widget(combo)

    def _get_value(self, *_):
        val = self.var.get()
        return self.keys_map.get(val)


class InfoRow(ttk.Frame):
    def __init__(self, parent, icon, text: str, url: str = None):
        super().__init__(parent)

        self.columnconfigure(1, weight=1)

        label = ttk.Label(self, image=icon)
        label.grid(row=0, column=0, padx=(5, 10), pady=4)

        text_label = ttk.Label(self, text=text, anchor="w")
        text_label.grid(row=0, column=1, sticky="w", pady=4)

        if url:
            text_label.configure(foreground="#176a8f", cursor="hand2")
            text_label.bind("<Button-1>", lambda e: self._open_url(url))

    def _open_url(self, url: str):
        import webbrowser
        webbrowser.open_new_tab(url)


class SettingsWidgets(ttk.Frame):
    settings_data: Dict[str, List[Tuple[str, ConfigKey, Union[type, Dict[str, Any]]]]] = {
        "Терминал": [
            ("Показывать терминал при старте программы:", ConfigKey.SHOW_TERMINAL,
             CheckboxFrame),
            ("Размер терминала по умолчанию:", ConfigKey.TERMINAL_SIZE, ComboboxFrame, {
                "Маленький внизу": TERM.SMALL.value,
                "Средний на 16 строк": TERM.MEDIUM.value,
                "На весь экран": TERM.LARGE.value
            }),
        ],
    }

    def __init__(
            self,
            parent: ttk.Frame,
            settings: Dict[ConfigKey, Any],
            version: str,
            github_url: str
    ):
        super().__init__(parent)
        self._icons = Icons()
        self._version = version
        self._github_url = github_url
        self.vars: Dict[ConfigKey, BaseFrame] = {}
        self._build(settings)
        self._build_about()
        self.grid_columnconfigure(0, weight=1)

    def _build(self, settings: Dict[ConfigKey, Any]):

        def remove_focus(event, widget=self):
            widget.focus_set()

        for section_title, rows in self.settings_data.items():
            section = ttk.LabelFrame(self, text=section_title)
            section.pack(fill="x", padx=10, pady=5, expand=True)
            section.columnconfigure(0, weight=1)  # вся строка BaseFrame должна растягиваться

            for row in rows:
                attr_name, key, widget_type, *args = row
                value = settings.get(key, "")

                if widget_type is ComboboxFrame:
                    widget = ComboboxFrame(section, key, value, attr_name, *args)
                else:
                    widget = widget_type(section, key, value, attr_name)

                widget.grid(sticky="ew", padx=5, pady=2)  # чтобы строка растягивалась
                self.vars[key] = widget

                widget.bind("<FocusIn>", remove_focus)
                widget.bind("<FocusOut>", remove_focus)

    def _build_about(self):
        section = ttk.LabelFrame(self, text="О программе")
        section.pack(fill="x", padx=10, pady=10, expand=True)
        section.columnconfigure(0, weight=1)

        version_row = InfoRow(section, self._icons[ICON.VERSION_24],
                              f"Версия программы: {self._version}")
        version_row.grid(row=0, column=0, sticky="ew")

        github_row = InfoRow(section, self._icons[ICON.CODE_24], "Страница на GitHub",
                             self._github_url)
        github_row.grid(row=1, column=0, sticky="ew")


class Settings(ttk.Frame):
    def __init__(
            self,
            parent: ttk.Frame,
            settings: Dict[ConfigKey, Any],
            version: str = "Неофициальная сборка",
            github_url: str = ""
    ):
        super().__init__(parent)
        self.configure_grid()

        self.scrolled = ScrolledFrame(parent=self)
        self.scrolled.grid(row=0, column=0, sticky="nsew")

        self.widgets = SettingsWidgets(
            parent=self.scrolled.content,
            settings=settings,
            version=version,
            github_url=github_url
        )
        self.scrolled.bind_scroll_events(self)
        self.widgets.grid(row=0, column=0, sticky="nsew")

    def configure_grid(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
