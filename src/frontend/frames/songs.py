from typing import List, Dict

import tkinter as tk

from ..widgets import Table
from ...enums import GROUP


class SongsTable(Table):
    def __init__(
            self,
            parent,
            group_id: GROUP,
            headers: List[str],
            data: List[List[str]],
            stretchable_column_indices: List[int],
            prev_cols_state: Dict[str, int],
            enable_tooltips: bool
    ):
        super().__init__(parent, group_id, headers, data, stretchable_column_indices,
                         prev_cols_state, enable_tooltips)
        self._create_add_to_report_button()

    def _create_add_to_report_button(self):
        # Кнопка "В отчёт"
        btn_report = tk.Button(
            self.table_panel.container,
            text="Add",
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
        pass