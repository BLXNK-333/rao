from typing import Dict

import tkinter as tk
from tkinter import ttk

from ...eventbus import Subscriber, EventBus
from ...enums import EventType, DispatcherType


class CardManager:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.TABLE.PANEL.EDIT_CARD, self.open_flashcard),
            (EventType.VIEW.TABLE.DT.EDIT_CARD, self.open_flashcard),
        ]

        for event_type, handler in subscriptions:
            EventBus.subscribe(
                event_type=event_type,
                subscriber=Subscriber(callback=handler, route_by=DispatcherType.TK)
            )

    def open_flashcard(self, card_data: Dict[str, str] = None):
        card = tk.Toplevel()
        card.geometry("500x200")