import logging
from typing import List, Dict, Set, Union, Tuple, Optional
from datetime import datetime

import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk
import tkinter.font as tkFont

from .widgets import UndoEntry, ToggleButton, HoverButton
from ..icons import Icons
from ...eventbus import Subscriber, EventBus, Event
from ...enums import EventType, DispatcherType, GROUP, ICON, STATE


class DataTable(ttk.Frame):
    size_states_map = {
        GROUP.SONGS_TABLE: STATE.SONGS_COL_SIZE,
        GROUP.REPORT_TABLE: STATE.REPORT_COL_SIZE
    }

    # region Initialization and Subscriptions

    def __init__(
            self,
            parent,
            group_id: GROUP,
            enable_tooltips: bool = False,
            show_table_end: bool = False
    ):
        super().__init__(parent)

        self._group_id = group_id
        self._dt = None
        self._enable_tooltips = enable_tooltips
        self._headers: List[str] = []
        self._stretchable_column_indices: Set[int] = set()
        self._show_table_end: bool = show_table_end
        self._table_len = 0

        self.estimated_column_widths: Dict[str, int] = {}
        self.user_defined_widths: Dict[str, int] = {}

        # Состояния
        self._col_sep_pressed = False

        # Текущее состояние сортировки: (column_name, direction),
        # где direction = 1 (▲), -1 (▼), 0 (нет)
        self._current_sort: Optional[Tuple[str, int]] = None
        self._sort_debounce_id = None
        self._sort_debounce_active = False

        self._heading_tooltip = None
        self._heading_tooltip_after_id = None
        self._heading_tooltip_texts = {}  # {column_id: tooltip_text}
        self._last_heading_col = ""

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.TABLE.BUFFER.CARD_UPDATED, self._insert_row_to),
            (EventType.VIEW.TABLE.BUFFER.INVISIBLE_ID, self._delete_invisible_row),
            (EventType.VIEW.TABLE.PANEL.DELETE_CARD, self._delete_selected_rows),
            (EventType.VIEW.TABLE.PANEL.EDIT_CARD, self._open_selected_row),
            (EventType.VIEW.TABLE.BUFFER.FILTERED_TABLE, self._filter_table),
            (EventType.VIEW.TABLE.PANEL.AUTO_SIZE, self._auto_size_widths)
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

    # endregion

    # region Table Creation and Setup

    def create_table(
            self,
            headers: List[str],
            data: List[List[str]],
            stretchable_column_indices: List[int]
    ):
        """Создание таблицы с заголовками и данными."""
        self._headers = headers
        self._stretchable_column_indices = set(stretchable_column_indices)
        self._table_len = len(data)

        self._setup_layout()
        self._create_dt()
        self._setup_styles()
        self._render_headers()
        self._fill_table(data)
        self._adjust_column_widths()
        self._apply_bindings()

    def _setup_layout(self):
        """Настройка сетки для виджета таблицы."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid(row=1, column=0, sticky="nsew")

    def _create_dt(self):
        """Создание ttk.Treeview и скроллбаров."""
        self.dt = ttk.Treeview(self, show="headings")
        self.dt.grid(row=0, column=0, sticky="nsew")

        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.dt.yview)
        self.dt.configure(yscrollcommand=self.scroll_y.set)
        self.scroll_y.grid(row=0, column=1, sticky="ns")

        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.dt.xview)
        self.dt.configure(xscrollcommand=scroll_x.set)
        scroll_x.grid(row=1, column=0, sticky="ew")

    def _setup_styles(self):
        """Настройка стилей для строк таблицы."""
        self.dt.tag_configure("oddrow", background="#f0f0f0")
        self.dt.tag_configure("evenrow", background="white")

    def _render_headers(self):
        """Настройка заголовков колонок и их событий."""
        self.dt.config(columns=self._headers)
        for idx, col in enumerate(self._headers):
            self.dt.heading(col, text=col, command=lambda c=col: self.on_header_click(c))
            self.dt.column(col, anchor="w", width=100, stretch=False)

    def _apply_bindings(self):
        """Привязка событий к виджету таблицы."""
        self.dt.bind("<Return>", self._open_selected_row)
        self.dt.bind("<Double-1>", self._open_selected_row)
        self.dt.bind("<ButtonPress-1>", self._on_mouse_press)
        self.dt.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.dt.bind("<Delete>", self._delete_selected_rows)
        self.bind("<Configure>", self._resize_columns)

        if self._enable_tooltips:
            self._bind_tooltip_events()

    # endregion

    # region Mouse Interaction and Sorting

    def _on_mouse_press(self, event):
        """Обработка нажатия мыши: фиксируем старт изменения ширины колонки."""
        if self.dt.identify_region(event.x, event.y) == "separator":
            self._col_sep_pressed = True
            self._initial_column_widths = {
                col: self.dt.column(col, option="width") for col in self._headers
            }

    def _on_mouse_release(self, event):
        """Обработка отпускания мыши: фиксируем изменения ширины и публикуем событие."""
        # region = self.dt.identify_region(event.x, event.y)
        if not hasattr(self, '_initial_column_widths'):
            return

        if self._col_sep_pressed:
            self._col_sep_pressed = False
            is_changed = False
            for col in self._headers:
                old = self._initial_column_widths.get(col)
                new = self.dt.column(col, option="width")
                if old is not None and old != new:
                    self.user_defined_widths[col] = new
                    is_changed = True

            if is_changed:
                self._publish_cols_state()
            self._resize_columns()

    def on_header_click(self, column: str):
        """Обработка клика по заголовку. Обертка, чтобы пустить через событийный цикл."""
        self.after(0, lambda col=column: self._on_header_click(col))

    def _on_header_click(self, column: str):
        """Обработка клика по заголовку колонки, переключение сортировки."""
        prev_col, prev_dir = self._current_sort if self._current_sort else (None, 0)

        if column != prev_col:
            # Сбрасываем предыдущую стрелку
            if prev_col:
                self.dt.heading(prev_col, text=prev_col)

            # Устанавливаем новую сортировку: сначала ▲
            self._current_sort = (column, 1)
            self.dt.heading(column, text=f"▲ {column}")
        else:
            if prev_dir == 1:
                # ▲ → ▼
                self._current_sort = (column, -1)
                self.dt.heading(column, text=f"▼ {column}")
            elif prev_dir == -1:
                # ▼ → убрать сортировку
                self._current_sort = None
                self.dt.heading(column, text=column)
            else:
                # Нет сортировки → ▲
                self._current_sort = (column, 1)
                self.dt.heading(column, text=f"▲ {column}")

        # Дебаунс
        if self._sort_debounce_id is not None and self._sort_debounce_active:
            try:
                self.after_cancel(self._sort_debounce_id)
            except Exception:
                pass  # таймер уже сработал
            self._sort_debounce_id = None

        self._sort_debounce_active = True
        self._sort_debounce_id = self.after(300, lambda: self._debounced_sort_publish())

    def _debounced_sort_publish(self):
        """Публикует событие сортировки с задержкой (дебаунс)."""
        self._sort_debounce_active = False
        self._sort_debounce_id = None
        EventBus.publish(
            Event(event_type=EventType.VIEW.TABLE.DT.SORT_CHANGED,
                  group_id=self._group_id),
            *self._get_sort_state()
        )

    def _get_sort_state(self) -> Tuple[int, str, int]:
        """Возвращает текущее состояние сортировки: (индекс, имя колонки, направление)."""
        if self._current_sort:
            col_name, direction = self._current_sort
            return self._headers.index(col_name), col_name, direction
        return -1, "", 0

    # endregion

    # region Column Width Management

    def _auto_size_widths(self):
        """Сбрасывает пользовательские ширины и автоматически подгоняет колонки."""
        self.user_defined_widths.clear()
        self._adjust_column_widths()
        self._resize_columns()
        self._publish_cols_state(auto_size=True)

    def _adjust_column_widths(self):
        """Подгоняет ширину колонок по содержимому и заголовкам, если нет
        пользовательских настроек."""

        font = tkFont.Font()
        padding = 0

        for idx, (col, char_count) in enumerate(self.estimated_column_widths.items()):
            if col in self.user_defined_widths:
                continue
            # Один вызов measure для строки длины N
            sample_text = "w" * char_count
            px_width = font.measure(sample_text) + padding
            self.user_defined_widths[col] = px_width
            self.dt.column(col, width=px_width, stretch=False)

    def _resize_columns(self, event=None):
        """Изменяет ширины колонок с учётом растягиваемых колонок и доступного пространства."""
        if not self._headers or not self.user_defined_widths:
            return

        total_width = self.winfo_width() - self.scroll_y.winfo_width()
        current_total = sum(
            self.user_defined_widths.get(col, 100) for col in self._headers
        )

        stretchables = [
            col for i, col in enumerate(self._headers)
            if i in self._stretchable_column_indices
        ]

        # Вычисляем итоговые ширины для всех колонок
        widths = {}
        if stretchables and total_width > current_total:
            extra = total_width - current_total
            per_column_extra = extra // len(stretchables)
        else:
            per_column_extra = 0
            stretchables = []

        for col in self._headers:
            base_width = self.user_defined_widths.get(col, 100)
            final_width = base_width + per_column_extra if col in stretchables else base_width
            widths[col] = (final_width, col in stretchables)

        # Применяем ширины за один проход
        for col, (width, stretch) in widths.items():
            self.dt.column(col, width=width, stretch=stretch)

    def _publish_cols_state(self, auto_size: bool = False):
        """Публикует событие изменения ширины колонок (ручное или авто)."""
        state_name = self.size_states_map.get(self._group_id)
        event_type = EventType.VIEW.TABLE.DT.AUTO_COL_SIZE \
            if auto_size else EventType.VIEW.TABLE.DT.MANUAL_COL_SIZE
        EventBus.publish(
            Event(
                event_type=event_type,
                group_id=self._group_id
            ),
            state_name, self.user_defined_widths
        )

    # endregion

    # region Table Rows Management

    def _insert_row_to(self, row: List[str], index: int):
        """Вставляет или обновляет строку в таблице по индексу."""
        card_id = row[0]
        if self.dt.exists(card_id):
            self.dt.delete(card_id)  # Удаляем старую строку
        else:
            self._table_len += 1

        # Вставляем в новую позицию
        self.dt.insert("", index, iid=card_id, values=row)
        self._recolor_rows()

        self.dt.selection_set(card_id)
        self.dt.focus(card_id)
        self.dt.see(card_id)

    def _delete_invisible_row(self, card_id: str):
        """Удаляет строку по идентификатору, если она существует."""
        if self.dt.exists(card_id):
            self.dt.delete(card_id)
            self._table_len -= 1
        self._recolor_rows()

    def _fill_table(self, data: List[List[str]]):
        """Обновляет содержимое таблицы с отфильтрованными данными."""
        self.dt.delete(*self.dt.get_children())
        self._table_len = len(data)
        for index, row in enumerate(data):
            self._insert_row(row, index)

    def _insert_row(self, row: List[str], index: int = None):
        """Вставляет строку в конец таблицы с заданным тегом (цветом) по индексу."""
        card_id = row[0]
        tag = self._get_tag(index)
        self.dt.insert("", "end", iid=card_id, values=row, tags=(tag,))

    def _get_tag(self, index: Optional[int]) -> str:
        """Обновляет цвет строк для зебры."""
        if index is None:
            index = self._table_len
        return "evenrow" if index % 2 == 0 else "oddrow"

    def _recolor_rows(self):
        """Перекрашивает строки таблицы в зависимости от их индекса (чётная/нечётная)."""
        for index, iid in enumerate(self.dt.get_children()):
            tag = self._get_tag(index)
            self.dt.item(iid, tags=(tag,))

    def _open_selected_row(self, event=None):
        """Обрабатывает открытие строки по Enter или двойному клику."""
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

    def _delete_selected_rows(self, event=None):
        """Удаляет выбранные строки."""
        selected_items = self.dt.selection()
        if not selected_items:
            return

        if not tk.messagebox.askyesno(
                "Уведомление", "Операция требует подтверждения."):
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
            self,
            rows: List[List[str]],
            is_full: bool = True
    ) -> None:
        """Обновляет таблицу, показывая только отфильтрованные данные
        и перекрашивает строки."""
        self._fill_table(rows)
        self._recolor_rows()
        self.scroll_to_bottom(rows, is_full)

    def scroll_to_bottom(self, rows: List[List[str]], is_full: bool):
        """Прокручивает в конец если задан self._show_table_end=True в конструкторе"""
        if self._show_table_end and rows:
            if is_full:
                self.dt.see(rows[-1][0])
            else:
                self.dt.see(rows[0][0])

    # endregion

    # start region HeaderTooltip
    def _on_mouse_motion_header(self, event):
        """Обработка движения мыши над заголовком, показ задержанного тултипа."""
        region = self.dt.identify_region(event.x, event.y)
        if region != "heading":
            self._cancel_heading_tooltip()
            return

        col_id = self.dt.identify_column(event.x)
        if not col_id or col_id == self._last_heading_col:
            return

        self._cancel_heading_tooltip()
        self._last_heading_col = col_id

        # задержка перед показом тултипа (в мс)
        self._heading_tooltip_after_id = self.after(
            500,
            lambda: self._show_heading_tooltip(col_id, event.x_root + 12,
                                               event.y_root + 10)
        )

    def _on_mouse_leave_header(self, _):
        """Отмена тултипа при уходе мыши с заголовка."""
        self._cancel_heading_tooltip()

    def _cancel_heading_tooltip(self):
        if self._heading_tooltip_after_id:
            self.after_cancel(self._heading_tooltip_after_id)
            self._heading_tooltip_after_id = None
        self._hide_heading_tooltip()
        self._last_heading_col = ""

    def _show_heading_tooltip(self, col_id, x, y):
        text = self._heading_tooltip_texts.get(col_id) or self.dt.heading(col_id).get(
            "text", "")
        self._hide_heading_tooltip()

        self._heading_tooltip = tk.Toplevel(self)
        self._heading_tooltip.wm_overrideredirect(True)
        self._heading_tooltip.wm_geometry(f"+{x}+{y}")

        # Можно добавить тень, эмулируя через рамку и цвет, но tkinter не поддерживает blur
        frame = ttk.Frame(self._heading_tooltip, style="Tooltip.TFrame")
        frame.pack()

        label = ttk.Label(
            frame,
            text=text,
            wraplength=400,
            style="CustomTooltip.TLabel",
            justify="left"
        )
        label.pack()

    def _hide_heading_tooltip(self):
        if self._heading_tooltip:
            self._heading_tooltip.destroy()
            self._heading_tooltip = None

    def _bind_tooltip_events(self):
        self.dt.bind("<Motion>", self._on_mouse_motion_header)
        self.dt.bind("<Leave>", self._on_mouse_leave_header)

    def _unbind_tooltip_events(self):
        self.dt.unbind("<Motion>")
        self.dt.unbind("<Leave>")

    # endregion


class TablePanel(ttk.Frame):
    # ICON COLOR = #29B6F6

    def __init__(self, parent: ttk.Frame, group_id: GROUP):
        super().__init__(parent)
        self._group_id = group_id
        self.search_var = tk.StringVar()
        self._debounce_id = None
        self.buttons = {}
        self.icons = Icons()
        self.search_entry = None

        # Основной контейнер строки поиска и кнопок
        self.container = ttk.Frame(self)
        self.container.pack(fill="x", padx=5, pady=5)

        self._create_buttons()
        self._create_entry()
        self.search_var.trace_add("write", self._on_search)

        self.grid(row=0, column=0, sticky="ew")

        self.subscribe()

    def subscribe(self):
        EventBus.subscribe(
            EventType.VIEW.TABLE.DT.MANUAL_COL_SIZE,
            Subscriber(
                callback=self.on_manual_size, group_id=self._group_id,
                route_by=DispatcherType.TABLE
            )
        )

    def _create_entry(self):
        self.search_entry = UndoEntry(self.container, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _create_btn(self, container: ttk.Frame, icon: ICON, command):
        btn = HoverButton(
            container,
            image=self.icons[icon],
            command=command,
            activebackground="#e7e7e7"  # Можно задать любой цвет для hover
        )
        btn.pack(side="left", padx=2)
        return btn

    def _create_buttons(self):
        """Создаёт кнопки справа от поля поиска"""
        container = ttk.Frame(self.container)
        container.pack(side="left")

        icons = [
            (ICON.ADD_CARD_24, self.add_card),
            (ICON.EDIT_CARD_24, self.edit_card),
            (ICON.DELETE_CARD_24, self.delete_card)
        ]

        for icon, command in icons:
            btn = self._create_btn(container, icon, command)
            self.buttons[icon] = btn

        auto_size_btn = ToggleButton(
            master=container,
            image_on=self.icons[ICON.AUTO_SIZE_ON_24],
            image_off=self.icons[ICON.AUTO_SIZE_OFF_24],
            initial_state=False,
            command=self.on_auto_size_applied,
            activebackground="#e7e7e7"
        )

        auto_size_btn.pack(side="left", padx=2)
        auto_size_btn.configure(state="disabled")
        self.buttons[ICON.AUTO_SIZE_ON_24] = auto_size_btn

        clear_btn = self._create_btn(container, ICON.ERASER_24, self.clear_entry)
        self.buttons[ICON.ERASER_24] = clear_btn

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

    def _clear_entry(self):
        if self.search_entry and self.search_entry._var.get():
            self.search_entry._var.set("")

    def clear_entry(self):
        self.after(0, lambda: self._clear_entry())

    def _on_search(self, *args):
        term = self.search_var.get().lower()
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, lambda: self.on_search(term))

    def on_search(self, term: str):
        EventBus.publish(
            Event(
                event_type=EventType.VIEW.TABLE.PANEL.SEARCH_VALUE,
                group_id=self._group_id
            ),
            term
        )

    def on_auto_size_applied(self):
        btn: ToggleButton = self.buttons[ICON.AUTO_SIZE_ON_24]
        btn.configure(state="disabled")

        EventBus.publish(
            Event(
                event_type=EventType.VIEW.TABLE.PANEL.AUTO_SIZE,
                group_id=self._group_id
            )
        )

    def on_manual_size(self, *args):
        btn: ToggleButton = self.buttons[ICON.AUTO_SIZE_ON_24]
        if str(btn["state"]) == "disabled":
            btn.toggle()
            btn.configure(state="normal")


class TableBuffer:
    def __init__(self, group_id: GROUP, max_history: int = 10):
        self._group_id = group_id
        self.original_data: Dict[str, List[str]] = {}
        self.sorted_keys: List[str] = []  # Отсортированные ключи
        self.header_map: Dict[str, str] = {}

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

            filtered_keys = [key for key in base_keys if
                             self._passes_filter(self.original_data.get(key, []))]
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
            data, self.current_filter_term == ""
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
                keys.sort(
                    key=lambda k: self._sort_key(
                        k, column_idx, self.header_map.get(column_name)),
                    reverse=(direction < 0)
                )
            self.sorted_keys = keys
        except Exception as e:
            self._logger.warning(f"Sort failed: {e}")
            self.sorted_keys = list(self.original_data.keys())

        self.history.clear()
        self.filter_data(term)

    def update_item(self, row: List[str]):
        card_id = row[0]
        self.original_data[card_id] = row

        term = self.current_filter_term.strip().lower()
        is_match = self._passes_filter(row)

        try:
            old_pos = self.sorted_keys.index(card_id)
            self.sorted_keys.pop(old_pos)
            was_present = True
        except ValueError:
            old_pos = None
            was_present = False

        if not is_match:
            self._publish_invisible_id(card_id)
            return

        pos = self._find_insert_position(card_id, was_present, old_pos)
        self.sorted_keys.insert(pos, card_id)

        self.history.clear()

        if not term:
            index = pos
        else:
            filtered_keys = [
                k for k in self.sorted_keys
                if self._passes_filter(self.original_data[k])
            ]
            try:
                index = filtered_keys.index(card_id)
            except ValueError:
                self._logger.warning(f"Card {card_id} not found in filtered list after insert")
                return

        EventBus.publish(
            Event(EventType.VIEW.TABLE.BUFFER.CARD_UPDATED, group_id=self._group_id),
            row, index
        )

    def delete_items(self, deleted_ids: List[str], _group_id: str):
        for item_id in deleted_ids:
            self.original_data.pop(item_id, None)
        self.history.clear()
        self.sorted_keys = [k for k in self.sorted_keys if k not in deleted_ids]

    def _publish_invisible_id(self, card_id: str):
        self._insert_sorted_key(card_id)
        self.history.clear()
        EventBus.publish(
            Event(EventType.VIEW.TABLE.BUFFER.INVISIBLE_ID, group_id=self._group_id),
            card_id
        )

    def _insert_sorted_key(self, card_id: str, was_present: bool = False,
                           old_pos: Optional[int] = None):
        pos = self._find_insert_position(card_id, was_present, old_pos)
        self.sorted_keys.insert(pos, card_id)

    def _find_insert_position(self, card_id: str, was_present: bool,
                              old_pos: Optional[int] = None) -> int:
        column_idx, column_name, direction = self.current_sort

        if direction == 0:
            return old_pos if was_present and old_pos is not None else len(self.sorted_keys)

        new_key = self._sort_key(card_id, column_idx, column_name)

        def get_key(k: str):
            return self._sort_key(k, column_idx, column_name)

        left, right = 0, len(self.sorted_keys)
        while left < right:
            mid = (left + right) // 2
            mid_key = get_key(self.sorted_keys[mid])
            if direction < 0:
                if mid_key > new_key:
                    left = mid + 1
                else:
                    right = mid
            else:
                if mid_key < new_key:
                    left = mid + 1
                else:
                    right = mid
        return left

    def _sort_key(self, card_id: str, column_idx: int, column_name: str):
        val = self.original_data[card_id][column_idx]

        if column_name in ("id", "play_count"):
            try:
                primary_key = int(val)
            except (ValueError, TypeError):
                primary_key = float('inf')

        elif column_name in {"duration", "play_duration", "total_duration", "time"}:
            # Поддержка форматов: "HH:MM:SS", "MM:SS", "SS"
            try:
                parts = list(map(int, val.strip().split(":")))

                if len(parts) == 3:
                    h, m, s = parts
                elif len(parts) == 2:
                    h, m, s = 0, parts[0], parts[1]
                elif len(parts) == 1:
                    h, m, s = 0, 0, parts[0]
                else:
                    raise ValueError("Too many parts")
                primary_key = h * 3600 + m * 60 + s

            except (ValueError, TypeError):
                primary_key = float('inf')

        elif column_name == "date":
            try:
                primary_key = datetime.strptime(val.strip(), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                primary_key = datetime.max.date()

        else:
            primary_key = str(val).lower()

        # Используем id как вторичный ключ (для стабильной сортировки)
        try:
            id_key = int(card_id)
        except (ValueError, TypeError):
            id_key = float('inf')

        return primary_key, id_key

    def _passes_filter(self, row: List[str]) -> bool:
        term = self.current_filter_term.strip().lower()
        return not term or any(term in cell.lower() for cell in row)


class Table(ttk.Frame):
    def __init__(
            self,
            parent,
            group_id: GROUP,
            header_map: Dict[str, str],
            data: List[List[str]],
            stretchable_column_indices: List[int],
            prev_cols_state: Dict[str, int],
            enable_tooltips: bool,
            show_table_end: bool
    ):
        super().__init__(parent)
        self._setup_layout()

        # Init
        self.group_id = group_id
        self.table_panel = TablePanel(
            parent=self,
            group_id=group_id
        )
        self.data_table = DataTable(
            parent=self,
            group_id=group_id,
            enable_tooltips=enable_tooltips,
            show_table_end=show_table_end
        )
        self.buffer = TableBuffer(group_id=group_id)

        # Configure
        SONGS_DICT = {row[0]: list(row) for row in data}
        HEADER_LIST = list(header_map.keys())
        self.buffer.original_data = SONGS_DICT
        self.buffer.header_map = header_map
        self.buffer.sorted_keys = list(SONGS_DICT.keys())
        self.data_table.estimated_column_widths = self._estimate_column_lengths(HEADER_LIST, data)

        self.data_table.create_table(
            headers=HEADER_LIST,
            data=data,
            stretchable_column_indices=stretchable_column_indices
        )

        if prev_cols_state is None:
            self.table_panel.on_auto_size_applied()
            prev_cols_state = {}

        elif self.data_table.user_defined_widths != prev_cols_state:
            self.table_panel.on_manual_size()

        self.data_table.user_defined_widths = prev_cols_state

        # Scroll to the table bottom
        self.data_table.scroll_to_bottom(rows=data, is_full=True)

    def _estimate_column_lengths(self, headers: List[str], data: List[List[str]],
                                sample_size: int = 20) -> Dict[str, int]:
        """Оценивает максимальную длину строки (в символах) для каждой колонки."""
        max_lengths = {col: len(col) for col in headers}
        sample = data[-sample_size:]  # последние sample_size строк

        for row in sample:
            for idx, col in enumerate(headers):
                if idx >= len(row):
                    continue  # пропускаем, если в строке меньше значений, чем колонок
                value = str(row[idx])
                max_lengths[col] = max(max_lengths[col], len(value))

        return max_lengths

    def _setup_layout(self):
        """Настраивает `grid` для размещения элементов."""
        self.grid_columnconfigure(0, weight=1)  # колонка с таблицей
        self.grid_rowconfigure(0, weight=0)     # панель управления
        self.grid_rowconfigure(1, weight=1)     # таблица
