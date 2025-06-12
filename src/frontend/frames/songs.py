from typing import List, Dict, Any

import tkinter as tk
from tkinter import messagebox

from ..widgets import Table
from ...eventbus import EventBus, Event
from ...enums import GROUP, EventType


class SongsTable(Table):
    def __init__(
            self,
            parent,
            group_id: GROUP,
            header_map: Dict[str, str],
            data: List[List[str]],
            stretchable_column_indices: List[int],
            prev_cols_state: Dict[str, int],
            enable_tooltips: bool,
            default_report_values: Dict[str, Any],
            show_table_end: bool
    ):
        super().__init__(parent, group_id, header_map, data, stretchable_column_indices,
                         prev_cols_state, enable_tooltips, show_table_end)

        self._default_report_values = default_report_values
        self._create_add_to_report_button()

    def _create_add_to_report_button(self):
        # Кнопка "В отчёт"
        btn_report = tk.Button(
            self.table_panel.container,
            text="В отчет",
            bg="#4CAF50",  # зелёный фон
            fg="white",  # белый текст
            activebackground="#45a049",  # фон при наведении
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.add_to_report,
            padx=12, pady=3,
        )
        btn_report.pack(side="right", padx=5)

    def add_to_report(self):
        self.after(0, lambda _=None: self._add_to_report())

    def _add_to_report(self):
        selected = self.data_table.dt.selection()
        if selected:
            card_id = selected[0]
        else:
            messagebox.showwarning(
                "Выбор песни",
                "Пожалуйста, выберите песню для добавления в отчёт.")
            return

        song = dict(zip(self.data_table._headers, self.buffer.original_data.get(card_id)))
        data = self._default_report_values.copy()

        data["Исполнитель"] = song["Исполнитель"]
        data["Название"] = song["Название"]
        data["Композитор"] = song["Композитор"]
        data["Автор текста"] = song["Автор текста"]
        data["Лэйбл"] = song["Лэйбл"]
        data["Общий хронометраж"] = song["Время"]
        data["Длительность звучания"] = song["Время"]

        EventBus.publish(
            Event(event_type=EventType.VIEW.TABLE.PANEL.ADD_CARD),
            GROUP.REPORT_TABLE, data, True
        )
