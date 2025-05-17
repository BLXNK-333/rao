from functools import partial
from typing import List, Dict, Set, Union
from collections.abc import ValuesView

import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk
import tkinter.font as tkFont

from ..widgets import UndoEntry
from ...eventbus import Subscriber, EventBus, Event
from ...enums import EventType, DispatcherType, GROUP, ICON
from ..icons.icon_map import Icons


class DataTable(ttk.Frame):
    def __init__(self, parent, group: GROUP):
        super().__init__(parent)

        self._group = group
        self._dt = None
        self._headers: List[str] = []
        self._user_defined_widths: Dict[str, int] = {}
        self._stretchable_column_indices: Set[int] = set()
        self._table_len = 0

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.TABLE.BUFFER.CARD_UPDATED, self._update_row),
            (EventType.VIEW.TABLE.PANEL.DELETE_CARD, self._delete_selected_rows),
            (EventType.VIEW.TABLE.PANEL.EDIT_CARD, self._open_selected_row),
            (EventType.VIEW.TABLE.BUFFER.FILTERED_TABLE, self._filter_table)
        ]
        for event_type, handler in subscriptions:
            EventBus.subscribe(
                event_type=event_type,
                subscriber=Subscriber(
                    callback=handler,
                    route_by=DispatcherType.TK,
                    group=self._group
                )
            )

    def create_table(
            self,
            headers: List[str],
            data: ValuesView[List[str]],
            stretchable_column_indices: List[int]
    ):
        self._headers = headers
        self._stretchable_column_indices = set(stretchable_column_indices)
        self._table_len = len(data)

        self._setup_layout()
        self._create_dt()
        self._setup_styles()
        self._render_headers()
        self._fill_table(data)
        self._adjust_column_widths()
        self.bind("<Configure>", self._resize_columns)

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid(row=1, column=0, sticky="nsew")

    def _create_dt(self):
        self.dt = ttk.Treeview(self, show="headings")
        self.dt.grid(row=0, column=0, sticky="nsew")

        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.dt.yview)
        self.dt.configure(yscrollcommand=self.scroll_y.set)
        self.scroll_y.grid(row=0, column=1, sticky="ns")

        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.dt.xview)
        self.dt.configure(xscrollcommand=scroll_x.set)
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.dt.bind("<Return>", self._open_selected_row)
        self.dt.bind("<Double-1>", self._open_selected_row)

    def _setup_styles(self):
        self.dt.tag_configure("oddrow", background="#f5f5f5")
        self.dt.tag_configure("evenrow", background="white")

    def _render_headers(self):
        self.dt.config(columns=self._headers)
        for col in self._headers:
            self.dt.heading(col, text=col)
            self.dt.column(col, anchor="w", width=100, stretch=False)

    def _adjust_column_widths(self, sample_size: int = 20):
        """Подгоняет ширину колонок по содержимому первых sample_size строк."""
        font = tkFont.Font()
        self._user_defined_widths = {}

        for col in self._headers:
            max_width = font.measure(col) + 20
            for iid in list(self.dt.get_children())[-sample_size:]:
                value = self.dt.set(iid, col)
                max_width = max(max_width, font.measure(value) + 10)
            self.dt.column(col, width=max_width, stretch=False)
            self._user_defined_widths[col] = max_width

    def _resize_columns(self, event=None):
        if not self._headers or not self._user_defined_widths:
            return

        total_width = self.winfo_width() - self.scroll_y.winfo_width()
        current_total = sum(
            self._user_defined_widths.get(col, 100) for col in self._headers)

        stretchables = [
            col for i, col in enumerate(self._headers) if
            i in self._stretchable_column_indices
        ]

        # 💡 Только если есть лишнее место, распределяем его
        if total_width <= current_total or not stretchables:
            for col in self._headers:
                self.dt.column(col, width=self._user_defined_widths[col], stretch=False)
            return

        # 💡 Распределяем излишек только если он есть
        extra = total_width - current_total
        per_column_extra = extra // len(stretchables)

        for i, col in enumerate(self._headers):
            base_width = self._user_defined_widths.get(col, 100)
            if i in self._stretchable_column_indices:
                self.dt.column(col, width=base_width + per_column_extra, stretch=True)
            else:
                self.dt.column(col, width=base_width, stretch=False)

    def _update_row(self, row: List[str]):
        card_id = row[0]
        # self._data[card_id] = row
        if self.dt.exists(card_id):
            self.dt.item(card_id, values=row)
        else:
            self._insert_row(row)
            self._table_len += 1

    def _fill_table(self, data: Union[List[List[str]], ValuesView[List[str]]]):
        self.dt.delete(*self.dt.get_children())
        self._table_len = len(data)
        for index, row in enumerate(data):
            self._insert_row(row, index)

    def _insert_row(self, row: List[str], index: int = None):
        card_id = row[0]
        tag = self._get_tag(index)
        self.dt.insert("", "end", iid=card_id, values=row, tags=(tag,))

    def _get_tag(self, index: int | None) -> str:
        if index is None:
            index = self._table_len
        return "evenrow" if index % 2 == 0 else "oddrow"

    def _recolor_rows(self):
        for index, iid in enumerate(self.dt.get_children()):
            tag = self._get_tag(index)
            self.dt.item(iid, tags=(tag,))

    def _open_selected_row(self, event=None):
        if event is not None:
            region = self.dt.identify_region(event.x, event.y)
            if region != "cell":
                return

        selected = self.dt.selection()
        if selected:
            card_id = selected[0]

            EventBus.publish(
                Event(event_type=EventType.VIEW.TABLE.DT.EDIT_CARD),
                card_id
            )

    def _delete_selected_rows(self):
        selected_items = self.dt.selection()
        if not selected_items:
            return

        if not tk.messagebox.askyesno("Confirmation", "Operation requires confirmation."):
            return

        deleted_ids = []
        for card_id in selected_items:

            self.dt.delete(card_id)
            deleted_ids.append(card_id)

        self._table_len -= len(deleted_ids)
        self._recolor_rows()

        EventBus.publish(
            Event(
                event_type=EventType.VIEW.TABLE.DT.DELETE_CARDS,
                group=self._group
            ),
            deleted_ids, self._group
        )

    def _filter_table(
            self, filtered: Union[List[List[str]], ValuesView[List[str]]]) -> None:
        self._fill_table(filtered)
        self._recolor_rows()


class TablePanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame, group: GROUP):
        super().__init__(parent)
        self._group = group
        self.search_var = tk.StringVar()
        self._debounce_id = None
        self.buttons = {}
        self.icons = Icons()

        # Основной контейнер строки поиска и кнопок
        self.container = ttk.Frame(self)
        self.container.pack(fill="x", padx=5, pady=5)

        self._create_buttons()
        self._create_entry()
        self._create_add_to_report_button()
        self.search_var.trace_add("write", self._on_search)

        self.grid(row=0, column=0, sticky="ew")

    def _create_entry(self):
        search_entry = UndoEntry(self.container, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _create_buttons(self):
        """Создаёт кнопки справа от поля поиска"""
        container = ttk.Frame(self.container)
        container.pack(side="left")

        icons = [
            (ICON.ADD_CARD_24, self.add_card),
            (ICON.EDIT_CARD_24, self.edit_card),
            (ICON.DELETE_CARD_24, self.delete_card),
        ]

        for icon, command in icons:
            btn = tk.Button(container, image=self.icons[icon], command=command,
                            relief="flat", activebackground="#d0d0ff")
            btn.pack(side="left", padx=2)
            self.buttons[icon] = btn

    def _create_add_to_report_button(self):
        # Кнопка "В отчёт"
        btn_report = tk.Button(
            self.container,
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

    def add_card(self):
        EventBus.publish(
            event=Event(
                event_type=EventType.VIEW.TABLE.PANEL.ADD_CARD,
                group=self._group)
        )

    def edit_card(self):
        EventBus.publish(
            event=Event(
                event_type=EventType.VIEW.TABLE.PANEL.EDIT_CARD,
                group=self._group)
        )

    def delete_card(self):
        EventBus.publish(
            event=Event(
                event_type=EventType.VIEW.TABLE.PANEL.DELETE_CARD,
                group=self._group)
        )

    def add_to_report(self):
        pass

    def _on_search(self, *args):
        term = self.search_var.get().lower()
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, partial(self.on_search, term))

    def on_search(self, term: str):
        EventBus.publish(
            Event(
                event_type=EventType.VIEW.TABLE.PANEL.SEARCH_VALUE,
                group=self._group
            ),
            term
        )


class TableBuffer:
    # TODO: Написать модуль card, и подключить базу данных, чтобы можно было
    #  протестировать логику, добавить логи.

    def __init__(self, group: GROUP, max_history: int = 10):
        self._group = group
        self.original_data: Dict[str, List[str]] = {}
        self.max_history = max_history
        self.history = []  # Список: (term, result)

        self.subscribe()

    def subscribe(self):
        subscribes = [
            (EventType.VIEW.TABLE.PANEL.SEARCH_VALUE, self.filter_data),
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self.delete_items),
            (EventType.BACK.DB.CARD_UPDATED, self.update_item)
        ]

        for event, handler in subscribes:
            EventBus.subscribe(
                event_type=event,
                subscriber=Subscriber(
                    callback=handler,
                    route_by=DispatcherType.SONG_TABLE,
                    group=self._group
                )
            )

    def filter_data(self, term: str):
        term = term.strip().lower()

        # Поиск подходящего буфера из истории
        if not term:
            filtered_data = self.original_data.values()
        else:
            base_data = self.original_data.values()
            for prev_term, prev_result in reversed(self.history):
                if term.startswith(prev_term):
                    base_data = prev_result
                    break

            filtered_data = [
                row for row in base_data
                if any(term in cell.lower() for cell in row)
            ]

        # Публикуем результат фильтрации
        EventBus.publish(
            Event(
                event_type=EventType.VIEW.TABLE.BUFFER.FILTERED_TABLE,
                group=self._group
            ),
            filtered_data,
        )

        # Обновляем историю
        self.history.append((term, filtered_data))
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def sort_data(self, column_idx: int, direction: int):
        pass

    def update_item(self, row: List[str]):
        card_id = row[0]
        self.original_data[card_id] = row
        # Тут буфер должен опубликовать для таблицы что-то, но будет зависеть от
        # логики которая будет написана позже, пока не ясно

    def delete_items(self, deleted_ids: List[str], _ident: str):
        for item_id in deleted_ids:
            self.original_data.pop(item_id)
        self.history.clear()
