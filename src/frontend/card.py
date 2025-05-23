import random
import string

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable

from .widgets import BaseWindow, ScrolledFrame, UndoText
from ..eventbus import Event, EventBus, Subscriber
from ..enums import EventType, DispatcherType, HEADER


class CardFields(ttk.Frame):
    """Отвечает за создание и управление полями ввода"""
    TEXT_STYLES = {
        "wrap": "word",
        "height": 1,
        "font": ("Arial", 11),
        "bg": "white"
    }

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

        if widget.edit_modified():
            # Только если реально есть модификация
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
            entry.config(state="disabled", bg="#f0f0f0", fg="#a0a0a0")

    def _add_text_field(self, index: int, key: str):
        text_entry = UndoText(self, initial_value=self.data.get(key, ""), resize=True,
                              styles_dict=self.TEXT_STYLES)
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


class CardButtons(ttk.Frame):
    def __init__(self, parent: ttk.Frame, editor: "CardEditor"):
        super().__init__(parent)
        self.editor = editor
        self.pack(fill="x", anchor="center", pady=10)
        self.save_btn = None
        self.cancel_btn = None
        self._create_bottom_buttons()

    def _create_bottom_buttons(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(anchor="center")

        self.save_btn = ttk.Button(btn_frame, text="Save", command=self.editor.on_save)
        self.save_btn.pack(side="left", padx=5)
        self.save_btn.state(["disabled"])

        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.editor.on_close)
        self.cancel_btn.pack(side="left", padx=5)

    def set_save_button_enabled(self, enabled: bool):
        """Включает или выключает кнопку Save."""
        if enabled:
            self.save_btn.state(["!disabled"])
        else:
            self.save_btn.state(["disabled"])


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
            data: Dict[str, str]
    ):
        super().__init__(parent)
        self.title("Edit card")
        self.geometry(self.geometry_map.get(HEADER(table)))
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.card_key = card_key
        self.table = table

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

        self.center_window()

    def get_id(self):
        return self.fields.data.get("ID", "")

    def set_id(self, card_id: str):
        self.fields.update_id(card_id)

    def on_save(self):
        data = self.fields.get_data()
        self.fields.data = data
        self.buttons.set_save_button_enabled(False)
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
        state = self.fields.has_changes()
        self.buttons.set_save_button_enabled(state)


class CardManager:
    def __init__(self, parent: tk.Frame):
        self.parent = parent
        self.opened_cards: Dict[str, CardEditor] = {}
        self.headers = {}

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.BACK.DB.CARD_DICT, self.open_card),
            (EventType.VIEW.TABLE.PANEL.ADD_CARD, self.open_card),
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self._del_card_ids),
            (EventType.VIEW.CARD.DESTROY, self._destroy_card),
            (EventType.BACK.DB.CARD_ID, self._update_card_id)
        ]

        for event, handler in subscriptions:
            EventBus.subscribe(
                event_type=event,
                subscriber=Subscriber(callback=handler, route_by=DispatcherType.TK)
            )

    def set_headers(self, value: Dict[HEADER, List[str]]):
        self.headers = value

    def _update_card_id(self, card_key: str, card_id: str):
        card = self.opened_cards.get(card_key)
        if card:
            card.set_id(card_id)

    def _del_card_ids(self, card_ids: List[str], _table: str):
        for_del = set(card_ids)
        to_remove = [card.card_key for card in self.opened_cards.values()
                     if card.get_id() in for_del]

        for card in to_remove:
            self._destroy_card(card)

    def _destroy_card(self, card_key: str):
        card = self.opened_cards.pop(card_key)
        card.destroy()

    def open_card(self, table: str, card_dict: Dict[str, str]):
        card_key = self.generate_card_key()
        card = CardEditor(
            parent=self.parent,
            card_key=card_key,
            table=table,
            headers=self.headers.get(table),
            data=card_dict
        )
        self.opened_cards[card_key] = card

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