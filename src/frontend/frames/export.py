import logging
from functools import partial
from typing import List, Tuple, Dict
import datetime

from tkinter import ttk, StringVar, filedialog
import tkinter as tk

from ..widgets import ScrolledFrame, UndoEntry
from ..icons.icon_map import Icons
from ...entities import MonthReport, QuarterReport


class ExportSection(ttk.Frame):
    def __init__(
            self,
            parent,
            title: str,
            labels: List[Tuple[str, str]],
            variables: Dict[str, StringVar],
            options: Dict[str, List[str]],
            export_callback
    ):
        super().__init__(parent)
        self.variables = variables
        self.options = options
        self.export_callback = export_callback
        self.icons = Icons()

        # Настройка сетки
        self.columnconfigure(1, weight=1)

        self.create_header(title)          # Заголовок + разделитель
        self.create_path_row()             # Строка выбора пути (Entry + кнопка)
        self.create_fields(labels)
        self.create_export_buttons()

    def create_header(self, title: str):
        ttk.Label(
            self, text=title, anchor="w", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 2))

        # Разделитель сразу после заголовка (row=1)
        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 10)
        )

    def create_path_row(self):
        # Строка выбора пути размещена ниже разделителя, row=2
        ttk.Label(self, text="Сохранить в:").grid(row=2, column=0, sticky="e", padx=(10, 15), pady=5)

        container = ttk.Frame(self)
        container.grid(row=2, column=1, columnspan=3, sticky="ew", pady=5, padx=(0, 10))
        container.columnconfigure(0, weight=1)

        entry = UndoEntry(container, textvariable=self.variables["path"])
        entry.grid(row=0, column=0, sticky="ew")
        btn = ttk.Button(container, text="…", width=2, command=self.choose_path)
        btn.grid(row=0, column=1, sticky="w", padx=(5, 0))

    def create_fields(self, labels: List[Tuple[str, str]]):
        """
        Создает комбобоксы с подписями в одну строку.
        """

        # Метка слева от контейнера с комбобоксами
        ttk.Label(self, text="Параметры:").grid(
            row=3, column=0, sticky="e", padx=(7, 20), pady=(0, 10)
        )

        # Контейнер для комбобоксов, правее метки
        fields_container = ttk.Frame(self)
        fields_container.grid(row=3, column=1, columnspan=3, sticky="w", padx=(0, 10),
                              pady=(0, 10))

        for idx, (label, var_name) in enumerate(labels):
            ttk.Label(fields_container, text=label).grid(
                row=0, column=2 * idx, sticky="e", padx=(0, 3)
            )

            combobox = ttk.Combobox(
                fields_container,
                textvariable=self.variables[var_name],
                values=self.options.get(var_name, []),
                state="readonly",
                width=12
            )
            combobox.grid(row=0, column=2 * idx + 1, sticky="w", padx=(0, 10))

            def remove_focus(event, widget=self):
                widget.focus_set()

            combobox.bind("<FocusIn>", remove_focus)
            combobox.bind("<FocusOut>", remove_focus)

    def create_export_buttons(self):
        """
        Создает кнопки экспорта с иконками, выровненные справа.
        """
        btn_container = ttk.Frame(self)
        btn_container.grid(row=3, column=2, sticky="e", padx=10, pady=(0, 10))

        formats = [
            ("xlsx", "#388E3C", "#2E7D32"),
            ("xls", "#388E3C", "#2E7D32"),
            ("csv", "#424242", "#616161")
        ]

        for text, bg_color, active_bg in formats:
            btn = tk.Button(
                btn_container,
                text=text,
                bg=bg_color,
                fg="white",
                activebackground=active_bg,
                font=("Segoe UI", 12, "bold"),
                relief="flat",
                command=partial(self.export_callback, text, self.variables),
                padx=12, pady=2,
            )
            btn.pack(side="left", padx=(2, 0))

    def choose_path(self):
        filename = filedialog.askdirectory(title="Выбор папки")
        if filename:
            self.variables["path"].set(filename)


class Export(ttk.Frame):
    MONTHS = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]

    def __init__(self, parent: ttk.Frame):
        super().__init__(parent)
        self.configure_grid()
        self._logger = logging.getLogger(__name__)

        self.inner = ttk.Frame(self)
        self.inner.grid(row=0, column=0, sticky="nsew")
        self.inner.columnconfigure(0, weight=1)
        self.inner.rowconfigure(0, weight=1)

        self.scrolled = ScrolledFrame(parent=self.inner)
        self.scrolled.grid(row=0, column=0, sticky="nsew")

        self.build_exports()
        self.scrolled.bind_scroll_events(self)

    def configure_grid(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def build_exports(self):
        container = self.scrolled.content
        container.columnconfigure(0, weight=1)
        now = datetime.datetime.now()

        # MONTHLY SECTION
        years = [str(y) for y in range(2022, now.year + 1)]

        month_vars = {
            "month": StringVar(),
            "year": StringVar(),
            "path": StringVar()
        }
        month_vars["month"].set(self.MONTHS[now.month - 1])
        month_vars["year"].set(str(now.year))

        monthly_section = ExportSection(
            parent=container,
            title="Экспорт ежемесячного отчёта",
            labels=[("Месяц:", "month"), ("Год:", "year")],
            variables=month_vars,
            options={"month": self.MONTHS, "year": years},
            export_callback=self.export_monthly
        )
        monthly_section.grid(row=0, column=0, sticky="ew")

        # QUARTERLY SECTION
        quarters = ["1 квартал", "2 квартал", "3 квартал", "4 квартал"]
        quarter_vars = {
            "quarter": StringVar(),
            "year": StringVar(),
            "path": StringVar()
        }
        quarter_vars["quarter"].set(quarters[(now.month - 1) // 3])
        quarter_vars["year"].set(str(now.year))

        quarterly_section = ExportSection(
            parent=container,
            title="Экспорт квартального отчёта",
            labels=[("Квартал:", "quarter"), ("Год:", "year")],
            variables=quarter_vars,
            options={"quarter": quarters, "year": years},
            export_callback=self.export_quarterly
        )
        quarterly_section.grid(row=1, column=0, sticky="ew", pady=(20, 0))

    def export_monthly(self, fmt: str, vars: dict):
        month_name = vars["month"].get()
        year_str = vars["year"].get()
        path = vars["path"].get()

        # Преобразование месяца из строки в номер (1–12)
        try:
            month_index = self.MONTHS.index(month_name) + 1
        except ValueError:
            self._logger.error(f"[MONTHLY] Invalid month: {month_name}")
            return

        export_report = MonthReport(
            month=month_index, year=int(year_str),
            file_format=fmt, save_path=path, data=[]
        )

        self._logger.info(f"[MONTHLY] Export parameters: {export_report}")

    def export_quarterly(self, fmt: str, vars: dict):
        quarter_str = vars["quarter"].get()
        year_str = vars["year"].get()
        path = vars["path"].get()

        # Преобразование квартала "1 квартал" → 1
        try:
            quarter_index = int(quarter_str[0])
        except (ValueError, IndexError):
            self._logger.error(f"[QUARTERLY] Invalid quarter: {quarter_str}")
            return

        export_report = QuarterReport(
            quarter=quarter_index, year=int(year_str),
            file_format=fmt, save_path=path, data=[]
        )

        self._logger.info(f"[QUARTERLY] Export parameters: {export_report}")
