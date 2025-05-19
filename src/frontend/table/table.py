import logging
from functools import partial
from typing import List, Dict, Set, Union, Tuple, Optional
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
    def __init__(self, parent, group_id: GROUP):
        super().__init__(parent)

        self._group_id = group_id
        self._dt = None
        self._headers: List[str] = []
        self._user_defined_widths: Dict[str, int] = {}
        self._stretchable_column_indices: Set[int] = set()
        self._table_len = 0

        # Текущее состояние сортировки: (column_name, direction),
        # где direction = 1 (▲), -1 (▼), 0 (нет)
        self._current_sort: Optional[Tuple[str, int]] = None

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.TABLE.BUFFER.CARD_UPDATED, self._highlight_row),
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
                    group_id=self._group_id
                )
            )

    def create_table(
            self,
            headers: List[str],
            data: Union[List[List[str]], ValuesView[List[str]]],
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
            self.dt.heading(col, text=col, command=partial(self._on_header_click, col))
            self.dt.column(col, anchor="w", width=100, stretch=False)

    def _on_header_click(self, column: str):
        """Обрабатывает клик по заголовку колонки и обновляет стрелки сортировки."""
        prev_col, prev_dir = self._current_sort if self._current_sort else (None, 0)

        if column != prev_col:
            # Сбрасываем предыдущую стрелку
            if prev_col:
                self.dt.heading(prev_col, text=prev_col)

            # Устанавливаем новую сортировку: сначала ▲
            self._current_sort = (column, 1)
            self.dt.heading(column, text=f"{column} ▲")
        else:
            if prev_dir == 1:
                # ▲ → ▼
                self._current_sort = (column, -1)
                self.dt.heading(column, text=f"{column} ▼")
            elif prev_dir == -1:
                # ▼ → убрать сортировку
                self._current_sort = None
                self.dt.heading(column, text=column)
            else:
                # Нет сортировки → ▲
                self._current_sort = (column, 1)
                self.dt.heading(column, text=f"{column} ▲")

        EventBus.publish(
            Event(event_type=EventType.VIEW.TABLE.DT.SORT_CHANGED, group_id=self._group_id),
            *self._get_sort_state()
        )

    def _get_sort_state(self) -> Tuple[int, str, int]:
        """Возвращает (index, column_name, direction)."""
        if self._current_sort:
            col_name, direction = self._current_sort
            return self._headers.index(col_name), col_name, direction
        return -1, "", 0

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

    def _highlight_row(self, row: List[str]):
        card_id = row[0]
        if self.dt.exists(card_id):
            self.dt.item(card_id, values=row)
            self.dt.selection_set(card_id)
            self.dt.focus(card_id)
            self.dt.see(card_id)

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
                self._group_id, card_id
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
                group_id=self._group_id
            ),
            deleted_ids, self._group_id
        )

    def _filter_table(
            self, filtered: Union[List[List[str]], ValuesView[List[str]]]) -> None:
        self._fill_table(filtered)
        self._recolor_rows()


class TablePanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame, group_id: GROUP):
        super().__init__(parent)
        self._group_id = group_id
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
            Event(event_type=EventType.VIEW.TABLE.PANEL.ADD_CARD),
            self._group_id, {}
        )

    def edit_card(self):
        EventBus.publish(
            event=Event(
                event_type=EventType.VIEW.TABLE.PANEL.EDIT_CARD,
                group_id=self._group_id)
        )

    def delete_card(self):
        EventBus.publish(
            event=Event(
                event_type=EventType.VIEW.TABLE.PANEL.DELETE_CARD,
                group_id=self._group_id)
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
                group_id=self._group_id
            ),
            term
        )


class TableBuffer:
    # TODO: Протестировать логику этого классы, возможно стоит покрыть тестами
    #  и писать через них, также возможно стоит оптимизировать логику.

    def __init__(self, group_id: GROUP, max_history: int = 10):
        self._group_id = group_id
        self.original_data: Dict[str, List[str]] = {}
        self.sorted_keys: List[str] = []  # Отсортированные ключи

        self.max_history = max_history
        self.history: List[Tuple[str, List[str]]] = []  # (term, list_of_keys)

        self._logger = logging.getLogger(__name__)

        # Текущие параметры сортировки и фильтрации
        self.current_sort: Tuple[int, str, int] = (0, "", 0)  # (column_idx, column_name, direction)
        self.current_filter_term: str = ""

        self.subscribe()

    def subscribe(self):
        for event, handler in [
            (EventType.VIEW.TABLE.PANEL.SEARCH_VALUE, self.filter_data),
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self.delete_items),
            (EventType.BACK.DB.CARD_VALUES, self.update_item),
            (EventType.VIEW.TABLE.DT.SORT_CHANGED, self.sort_data),
        ]:
            EventBus.subscribe(
                event_type=event,
                subscriber=Subscriber(
                    callback=handler,
                    route_by=DispatcherType.TABLE,
                    group_id=self._group_id,
                )
            )

    def filter_data(self, term: str):
        term = term.strip().lower()
        self.current_filter_term = term  # сохраняем текущий фильтр

        base_keys = self.sorted_keys.copy()

        if term:
            for prev_term, prev_keys in reversed(self.history):
                if term.startswith(prev_term):
                    base_keys = prev_keys
                    break

            filtered_keys = [
                key for key in base_keys
                if any(term in cell.lower() for cell in self.original_data.get(key, []))
            ]
        else:
            filtered_keys = base_keys

        filtered_data = [self.original_data[key] for key in filtered_keys]

        self._publish_filtered(filtered_data)
        self._update_history(term, filtered_keys)

    def _publish_filtered(self, data: List[List[str]]):
        EventBus.publish(
            Event(
                event_type=EventType.VIEW.TABLE.BUFFER.FILTERED_TABLE,
                group_id=self._group_id
            ),
            data
        )

    def _update_history(self, term: str, keys: List[str]):
        self.history.append((term, keys))
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def sort_data(self, column_idx: int, column_name: str, direction: int):
        self.current_sort = (column_idx, column_name, direction)
        term = self.current_filter_term

        try:
            keys = list(self.original_data.keys())

            if direction:
                if column_name == "ID":
                    keys.sort(
                        key=lambda k: int(self.original_data[k][column_idx]),
                        reverse=(direction < 0))
                else:
                    keys.sort(
                        key=lambda k: self.original_data[k][column_idx].lower(),
                        reverse=(direction < 0))

            self.sorted_keys = keys
        except Exception as e:
            self._logger.warning(f"Sort failed: {e}")
            self.sorted_keys = list(self.original_data.keys())

        self.history.clear()
        self.filter_data(term)

    def update_item(self, row: List[str]):
        card_id = row[0]
        self.original_data[card_id] = row

        column_idx, column_name, direction = self.current_sort
        self.sort_data(column_idx, column_name, direction)

        EventBus.publish(Event(
            event_type=EventType.VIEW.TABLE.BUFFER.CARD_UPDATED,
            group_id=self._group_id
        ), row)

    def delete_items(self, deleted_ids: List[str], _group_id: str):
        for item_id in deleted_ids:
            self.original_data.pop(item_id, None)
        self.history.clear()

        # Обновляем sorted_keys после удаления
        self.sorted_keys = [k for k in self.sorted_keys if k not in deleted_ids]


class Table(ttk.Frame):
    def __init__(self, parent, group_id: GROUP):
        super().__init__(parent)
        self._setup_layout()

        self.table_panel = TablePanel(parent=self, group_id=group_id)
        self.data_table = DataTable(parent=self, group_id=group_id)
        self.buffer = TableBuffer(group_id=group_id)

    def _setup_layout(self):
        """Настраивает `grid` для размещения элементов."""
        self.grid_columnconfigure(0, weight=1)  # колонка с таблицей
        self.grid_rowconfigure(0, weight=0)     # панель управления
        self.grid_rowconfigure(1, weight=1)     # таблица