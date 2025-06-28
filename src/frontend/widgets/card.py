import random
import string
import copy

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable, Union, Optional

from .widgets import BaseWindow, ScrolledFrame, UndoText, ToggleButton
from ..icons import Icons
from ...eventbus import Event, EventBus, Subscriber
from ...enums import EventType, DispatcherType, HEADER, ICON


class CardFields(ttk.Frame):
    """Отвечает за создание и управление полями ввода"""
    BAD_FIELD_HIGHLIGHT = "#ffd2da"

    def __init__(
            self,
            parent: tk.Toplevel,
            headers: List[str],
            data: Dict[str, str],
            change_callback: Callable
    ):
        super().__init__(parent)

        self.headers = headers
        self.data = data
        self.entries = {}
        self.change_callback = change_callback
        self.pack(fill="both", expand=True, padx=5, pady=10)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(len(self.headers), weight=1)

        self._create_fields()
        self._disable_entry("ID")
        self._reset_modified_flags()
        self._bind_change_events()

    def _bind_change_events(self):
        """Подключает обработчики событий изменения полей."""
        for widget in self.entries.values():
            widget.bind("<<Modified>>", self._on_modified)

    def _reset_modified_flags(self):
        """Сбрасывает флаги модификации для всех полей после полной инициализации окна."""
        for widget in self.entries.values():
            widget.edit_modified(False)

    def _on_modified(self, event):
        widget = event.widget

        # Только если реально есть модификация
        if widget.edit_modified():
            # Сброс фона при изменении
            try:
                if widget.cget("bg") != "white":
                    widget.config(bg="white")
            except tk.TclError:
                pass
            self.change_callback()
            widget.edit_modified(False)  # Сбрасываем флаг только после обработки

    def _create_fields(self):
        """Создаёт UI для полей ввода"""
        for i, key in enumerate(self.headers):
            ttk.Label(self, text=key, style="Custom.TLabel").grid(
                row=i, column=0, sticky="w", pady=2
            )
            self._add_text_field(i, key)

    def _disable_entry(self, key: str):
        """Отключает Text-поле с изменением цвета."""
        entry = self.entries[key]
        if entry:
            entry.config(state="disabled", bg="#f7f7f7", fg="#a0a0a0")

    def _add_text_field(self, index: int, key: str):
        text_entry = UndoText(self, initial_value=self.data.get(key, ""), resize=True)
        text_entry.grid(row=index, column=1, sticky="ew", padx=5, pady=2)
        self.entries[key] = text_entry

    def get_data(self):
        """Собирает данные из полей"""
        return {k: self.entries[k].get("1.0", "end").strip() for k in self.headers}

    def has_changes(self):
        """Проверяет, были ли изменения в полях относительно оригинальных данных."""
        current = self.get_data()
        return any(self.data.get(k, "") != v for k, v in current.items())

    def update_id(self, card_id: str):
        """Обновляет значение ID в заблокированном поле."""
        entry = self.entries["ID"]
        self.data["ID"] = card_id

        # Временно включаем для редактирования
        entry.config(state="normal")
        entry.delete("1.0", "end")
        entry.insert("1.0", card_id)
        entry.config(state="disabled")
        entry.edit_modified(False)

    def highlight_bad_fields(self, fields_map: Dict[str, bool]):
        """Подсвечивает поля с ошибками розовым, остальные — белым."""
        for field, widget in self.entries.items():
            if field == "ID":
                continue

            is_valid = fields_map.get(field, True)
            new_color = self.BAD_FIELD_HIGHLIGHT if not is_valid else "white"
            try:
                widget.config(bg=new_color)
            except tk.TclError:
                # Иногда текстовые поля в readonly могут кидать ошибку — игнорируем
                pass

    def update_fields(self, card_dict: Dict[str, str]):
        """Обновляет содержимое всех полей ввода и внутренние данные."""
        self.data = card_dict

        for key in self.headers:
            value = card_dict.get(key, "")
            entry = self.entries.get(key)
            if entry:
                # Временно разблокируем, если поле заблокировано
                state = entry.cget("state")
                if state == "disabled":
                    entry.config(state="normal")

                entry.delete("1.0", "end")
                entry.insert("1.0", value)
                entry.edit_modified(False)  # Сброс флага модификации

                # Вернём блокировку обратно
                if key == "ID":
                    entry.config(state="disabled")

                # Сброс цвета
                try:
                    entry.config(bg="white")
                except tk.TclError:
                    pass


class CardButtons(ttk.Frame):
    def __init__(self, parent: ttk.Frame, editor: "CardEditor"):
        super().__init__(parent)
        self._icons = Icons()
        self.editor = editor

        self._create_widgets()
        self._layout_widgets()

        self.pack(fill="x", pady=10)

    def _create_widgets(self):
        # Левый блок
        self.left_frame = ttk.Frame(self)
        self.pin_btn = ToggleButton(
            self.left_frame,
            image_on=self._icons[ICON.PIN_ON_24],
            image_off=self._icons[ICON.PIN_OFF_24],
            initial_state=False,
            command=self.editor.toggle_pin
        )
        self.transparency_btn = ToggleButton(
            self.left_frame,
            image_on=self._icons[ICON.EYE_24],
            image_off=self._icons[ICON.HIDDEN_24],
            initial_state=False,
            command=self.editor.toggle_transparency
        )

        # Центр
        self.center_frame = ttk.Frame(self)
        self.inner_center = ttk.Frame(self.center_frame)
        self.save_btn = ttk.Button(self.inner_center, text="Сохранить",
                                   command=self.editor.on_save)
        self.save_btn.state(["disabled"])
        self.cancel_btn = ttk.Button(self.inner_center, text="Отмена",
                                     command=self.editor.on_close)

        # Правый "заполнитель"
        self.right_filler = ttk.Frame(self, width=0)

    def _layout_widgets(self):
        # Сборка левого блока
        self.left_frame.pack(side="left", padx=10)
        self.pin_btn.pack(side="left", padx=(0, 5))
        self.transparency_btn.pack(side="left", padx=(5, 0))

        # Центр
        self.center_frame.pack(side="left", expand=True)
        self.inner_center.pack(anchor="center")
        self.save_btn.pack(side="left", padx=5)
        self.cancel_btn.pack(side="left", padx=5)

        # Правый заполнитель
        self.right_filler.pack(side="right", padx=10)
        self.after(10, lambda _=None: self._sync_filler_width())

    def _sync_filler_width(self):
        """Выравнивает правый фрейм по ширине с левым, для центрирования."""
        width = self.left_frame.winfo_width()
        self.right_filler.config(width=width)

    def set_save_button_enabled(self, enabled: bool):
        """Включает или выключает кнопку Save."""
        self.save_btn.state(["!disabled"] if enabled else ["disabled"])


class CardEditor(tk.Toplevel, BaseWindow):
    geometry_map = {
        HEADER.SONGS: "500x270",
        HEADER.REPORT: "500x440"
    }

    def __init__(
            self,
            parent: ttk.Frame,
            card_key: str,
            table: str,
            headers: List[str],
            data: Dict[str, str],
            transparent_alpha: Union[float, int],
            pinned: bool = False,
            unlock_save: bool = False
    ):
        """
        Редактор карточки.

        :param parent: Родительский элемент.
        :param card_key: Сгенерированный ключ открытой карточки, типа "ABCD".
        :param table: Идентификатор таблицы к которой принадлежит карточка.
        :param headers: Заголовки для названия полей.
        :param data: Словарь с данными, ключи как в headers
        :param transparent_alpha: Степень прозрачности от 0 до 1, чем меньше, тем прозрачнее.
        :param pinned: Закрепить карточку при открытии.
        :param unlock_save: Разблокировать кнопку "Сохранить", пока карточка не получит ID.
        """
        super().__init__(parent)
        self.withdraw()
        self.title("Редактировать карточку")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.card_key = card_key
        self.table = table
        self.is_new = not bool(data.get("ID"))
        self.unlock_save = unlock_save
        self._pinned = pinned or False

        # Прозрачность
        self.is_transparent = False
        self.default_alpha = 1.0
        self.transparent_alpha = transparent_alpha

        # Основной контейнер
        self.scrolled = ScrolledFrame(self)
        self.scrolled.grid(row=0, column=0, sticky="nsew")

        self.fields = CardFields(
            self.scrolled.content,
            headers,
            data,
            change_callback=self.update_save_button_state  # передаём колбэк
        )
        self.buttons = CardButtons(self.scrolled.content, editor=self)
        self.scrolled.bind_scroll_events()

        # Настройка растяжения
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        geometry = self.geometry_map.get(HEADER(table))
        if self._pinned:
            self.attributes("-topmost", True)
            self.buttons.pin_btn.toggle()

        self.show_centered(geometry)

    def get_id(self):
        return self.fields.data.get("ID", "")

    def set_id(self, card_id: str):
        self.fields.update_id(card_id)

    def on_save(self):
        for widget in self.fields.entries.values():
            widget.event_generate("<<Modified>>")
            widget.update_idletasks()

        data = self.fields.get_data()
        EventBus.publish(
            Event(event_type=EventType.VIEW.CARD.SAVE),
            self.card_key, self.table, data
        )

    def on_close(self):
        EventBus.publish(
            Event(event_type=EventType.VIEW.CARD.DESTROY),
            self.card_key
        )

    def update_save_button_state(self):
        """Обновляет состояние кнопки Save в зависимости от наличия изменений."""
        if self.unlock_save and not self.get_id():
            return
        self.unlock_save = False
        state = self.fields.has_changes()
        if self.get_id() or self.is_new:
            self.buttons.set_save_button_enabled(state)

    def toggle_pin(self):
        """Переключает режим 'поверх всех окон'."""
        self._pinned = not self._pinned
        try:
            self.attributes("-topmost", self._pinned)
        except Exception:
            pass  # если editor не поддерживает (в rare case)

    def toggle_transparency(self):
        self.is_transparent = not self.is_transparent
        alpha = self.transparent_alpha if self.is_transparent else self.default_alpha
        self.wm_attributes("-alpha", alpha)


class CardManager:
    def __init__(
            self,
            parent: tk.Frame,
            default_card_values: Dict[HEADER, Dict[str, str]],
            card_transparent_value: int = 85,
            card_pin = False
    ):
        self.parent = parent
        self.opened_cards: Dict[str, CardEditor] = {}
        self.default_values = default_card_values
        self._card_transparent_value = card_transparent_value
        self._set_card_transparent_value(card_transparent_value)
        self._card_pin = card_pin

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.BACK.DB.CARD_DICT, self._on_card_dict),
            (EventType.VIEW.TABLE.PANEL.ADD_CARD, self._open_card),
            (EventType.VIEW.TABLE.DT.CLONE_ITEM, self._open_card),
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self._del_card_ids),
            (EventType.VIEW.CARD.DESTROY, self._destroy_card),
            (EventType.BACK.DB.CARD_ID, self._update_card_id),
            (EventType.BACK.DB.VALIDATION, self._highlight_bad_fields),
            (EventType.VIEW.SETTINGS.CARD_TRANSPARENCY, self._set_card_transparent_value),
            (EventType.VIEW.SETTINGS.CARD_PIN, self._set_card_pin)
        ]

        for event, handler in subscriptions:
            EventBus.subscribe(
                event_type=event,
                subscriber=Subscriber(callback=handler, route_by=DispatcherType.TK)
            )

    def _update_card_id(self, card_key: str, card_id: str):
        card = self.opened_cards.get(card_key)
        if card:
            card.set_id(card_id)

    def _set_card_transparent_value(self, value: int):
        self._card_transparent_value = round(value / 100, 2)

    def _set_card_pin(self, value: bool):
        self._card_pin = value

    def _del_card_ids(self, card_ids: List[str], _table: str):
        for_del = set(card_ids)
        to_remove = [card.card_key for card in self.opened_cards.values()
                     if card.get_id() in for_del]

        for card in to_remove:
            self._destroy_card(card)

    def _destroy_card(self, card_key: str):
        card = self.opened_cards.pop(card_key)
        card.withdraw()
        card.update_idletasks()
        card.destroy()

    def _on_card_dict(self, card_key: str, table: str, card_dict: Dict[str, str]):
        """Тут реагирует на рассылку словаря карточки, если карточка открыта, обновляет.
        Иначе, открывает новую."""
        if card_key:
            self._update_card(card_key, card_dict)
        else:
            self._open_card(table, card_dict)

    def _update_card(self, card_key: str, card_dict: Dict[str, str]):
        open_card = self.opened_cards.get(card_key)
        if open_card:
            open_card.is_new = False
            open_card.fields.update_fields(card_dict)
            open_card.buttons.set_save_button_enabled(False)

    def _open_card(self, table: str, card_dict: Dict[str, str],
                   unlock_save: bool = False):
        card_key = self.generate_card_key()
        table_name = HEADER(table)
        headers = list(self.default_values.get(table_name).keys())
        data = card_dict if card_dict else copy.deepcopy(
            self.default_values.get(table_name))

        card = CardEditor(
            parent=self.parent,
            card_key=card_key,
            table=table,
            headers=headers,
            data=data,
            transparent_alpha=self._card_transparent_value,
            pinned=self._card_pin,
            unlock_save=unlock_save
        )
        self.opened_cards[card_key] = card
        if unlock_save:
            card.buttons.set_save_button_enabled(True)

    def generate_card_key(self, length=4, max_attempts=10) -> str:
        """
        Generates a unique alphabetical ID not present in self.opened_cards.
        """
        for _ in range(max_attempts):
            comb = ''.join(random.choices(string.ascii_uppercase, k=length))
            if comb not in self.opened_cards:
                return comb
        raise RuntimeError(
            f"Failed to generate a unique ID after {max_attempts} attempts")

    def _highlight_bad_fields(self, card_key: str, validation_result: Dict[str, bool]):
        """
        Подсвечивает не валидные поля в открытой карточке.

        :param card_key: Ключ открытой карточки.
        :param validation_result: Словарь, где ключ - название поле, а значение - статус
        """
        open_card = self.opened_cards.get(card_key)

        if all(validation_result.values()):
            # Тут закроет карточку сразу после сохранения.
            self._destroy_card(card_key)
        else:
            open_card.fields.highlight_bad_fields(validation_result)

    def has_open_cards(self) -> bool:
        """Проверяет есть ли не сохраненные карточки, среди открытых."""
        return any(card.fields.has_changes() for card in self.opened_cards.values())

    def lift_all_cards(self):
        """Поднять все открытые карточки на передний план."""
        for card in self.opened_cards.values():
            card.lift()
