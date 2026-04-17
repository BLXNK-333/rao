import sys
from typing import List, Dict, Any, Optional, Tuple

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ..widgets import Table
from ..style import CONTEXT_MENU_STYLES
from ...eventbus import EventBus, Event
from ...enums import GROUP, EventType


class TableWrapper(ttk.Frame):
    def __init__(
            self,
            parent,
            group_id: GROUP,
            header_map: Dict[str, str],
            data: List[List[str]],
            stretchable_column_indices: List[int],
            enable_tooltips: bool,
            show_table_end: bool,
            prev_cols_state: Optional[Dict[str, int]] = None,
            sort_key_state: Optional[Tuple[str, int, str]] = None
    ):
        super().__init__(parent)
        self.configure_grid()

        self.table = Table(
            self, group_id, header_map, data, stretchable_column_indices,
            enable_tooltips, show_table_end, prev_cols_state, sort_key_state,
        )
        self.table.grid(row=0, column=0, sticky="nsew", pady=(3, 0))

        # Создаем дополнительные секции для контекстного меню.
        self.table.data_table.context_menu.add_separator()
        copy_menu = tk.Menu(
            self.table.data_table.context_menu,
            tearoff=0,
            **CONTEXT_MENU_STYLES
        )

        for header in self.table.data_table._headers:
            if header.lower() == "id":
                continue

            copy_menu.add_command(
                label=f"- {header.lower()}",
                command=lambda k=header: self._get_field_value(k)
            )

        self.table.data_table.context_menu.add_cascade(
            label="Копировать",
            menu=copy_menu
        )

    def _get_field_value(self, key: str):
        selected_items = self.table.data_table.dt.selection()
        original_id = selected_items[0]
        data = dict(zip(
            self.table.data_table._headers,
            self.table.data_table.dt.item(original_id, "values")
        ))
        self.clipboard_clear()
        self.clipboard_append(data.get(key, ""))

    def configure_grid(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)


class ReportTable(TableWrapper):
    pass


class SongsTable(TableWrapper):
    def __init__(
            self,
            parent,
            group_id: GROUP,
            header_map: Dict[str, str],
            data: List[List[str]],
            stretchable_column_indices: List[int],
            enable_tooltips: bool,
            show_table_end: bool,
            default_report_values: Dict[str, Any],
            prev_cols_state: Optional[Dict[str, int]] = None,
            sort_key_state: Optional[Tuple[str, int, str]] = None
    ):
        super().__init__(
            parent, group_id, header_map, data, stretchable_column_indices,
            enable_tooltips, show_table_end, prev_cols_state, sort_key_state
        )
        # Создаем дополнительную кнопку "В отчет".
        self._default_report_values = default_report_values
        self._create_add_to_report_button()

        self.table.data_table.context_menu.add_separator()
        self.table.data_table.context_menu.add_command(
            label="В отчет", command=self.add_to_report)

    def _create_add_to_report_button(self):
        # Кнопка "В отчёт"
        pady = 0 if sys.platform == "win32" else 3
        btn_report = tk.Button(
            self.table.table_panel.container,
            text="В отчет",
            bg="#16a085",  # зелёный фон
            fg="white",  # белый текст
            activebackground="#138d75",  # фон при наведении
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            command=self.add_to_report,
            padx=12, pady=pady,
        )
        btn_report.pack(side="right", padx=5)

    def add_to_report(self):
        selected = self.table.data_table.dt.selection()
        if selected:
            card_id = selected[0]
        else:
            messagebox.showwarning(
                "Выбор песни",
                "Пожалуйста, выберите песню для добавления в отчёт.")
            return

        song = dict(zip(
            self.table.data_table._headers,
            self.table.buffer.original_data.get(card_id)
        ))
        data = self._default_report_values.copy()

        data["Исполнитель"] = song["Исполнитель"]
        data["Название"] = song["Название"]
        data["Композитор"] = song["Композитор"]
        data["Автор текста"] = song["Автор текста"]
        data["Лэйбл"] = song["Лэйбл"]
        data["Общий хронометраж"] = song["Общий хронометраж"]
        data["Длительность звучания"] = song["Общий хронометраж"]

        EventBus.publish(
            Event(event_type=EventType.VIEW.TABLE.PANEL.ADD_CARD),
            GROUP.REPORT_TABLE, data, True
        )
