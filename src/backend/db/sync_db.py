from typing import Dict, List

from .database import Database
from .settings import (
    get_headers,
    map_ui_to_model_fields,
    map_db_rows_to_view_order
)
from ...enums import EventType, DispatcherType, HEADER, GROUP
from ...eventbus import Event, Subscriber, EventBus


class SyncDB:
    def __init__(self):
        self.db = Database()
        self.subscribe()

    def subscribe(self):
        handlers = [
            (EventType.VIEW.UI.CLOSE_WINDOW, self.close_connection),
            (EventType.VIEW.TABLE.DT.EDIT_CARD, self.get_card),
            (EventType.VIEW.CARD.SAVE, self.save_card),
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self.delete_card)
        ]

        for event, handler in handlers:
            EventBus.subscribe(
                event_type=event,
                subscriber=Subscriber(
                    callback=handler, route_by=DispatcherType.DB
                )
            )

    def get_all_rows(self, table_name: str):
        all_rows = self.db.get_all_rows(table_name)
        remapped_rows = map_db_rows_to_view_order(table_name, all_rows)
        return remapped_rows

    def get_report(self):
        pass

    def get_card(self, table_name: str, card_id: str):
        db_row = self.db.get_card(table_name, card_id)
        remapped_row = map_db_rows_to_view_order(table_name, [db_row])[0]
        card_data = dict(zip(get_headers(HEADER(table_name)), remapped_row))
        EventBus.publish(
            Event(event_type=EventType.BACK.DB.CARD_DICT),
            table_name, card_data
        )

    def save_card(self, card_key: str, table_name: str, data: Dict[str, str]):
        card_id = data.get("ID")
        remapped_data = map_ui_to_model_fields(data=data, table_name=HEADER(table_name))

        if card_id:
            self.db.update_card(card_id=card_id, table_name=table_name, payload=remapped_data)
        else:
            card_id = self.db.add_card(table_name=table_name, payload=remapped_data)
            data["ID"] = card_id
            EventBus.publish(Event(EventType.BACK.DB.CARD_ID), card_key, card_id)

        EventBus.publish(Event(
            event_type=EventType.BACK.DB.CARD_VALUES,
            group_id=GROUP(table_name)
        ), list(data.values()))

    def delete_card(self, deleted_ids: List[str], table_name: str):
        self.db.delete_card(deleted_ids, table_name)

    def close_connection(self):
        self.db.close()