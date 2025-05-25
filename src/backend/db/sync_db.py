from typing import Dict, List, Any

from .database import Database
from .settings import (
    get_headers,
    map_ui_to_model_fields,
    map_db_rows_to_view_order,
    convert_all_rows
)
from ...enums import EventType, DispatcherType, HEADER, GROUP, STATE
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
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self.delete_card),
            (EventType.VIEW.TABLE.DT.MANUAL_COL_SIZE, self.set_state),
            (EventType.VIEW.TABLE.DT.AUTO_COL_SIZE, self.set_state),
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
        remapped_rows = convert_all_rows(table_name, all_rows)
        return remapped_rows

    def get_report(self):
        pass

    def get_card(self, table_name: str, card_id: str):
        db_row = self.db.get_card(table_name, card_id)
        remapped_row = map_db_rows_to_view_order(table_name, db_row)
        EventBus.publish(
            Event(event_type=EventType.BACK.DB.CARD_DICT),
            table_name, remapped_row
        )

    def save_card(self, card_key: str, table_name: str, data: Dict[str, str]):
        card_id = data.get("ID")
        remapped_data = map_ui_to_model_fields(table_name=HEADER(table_name), data=data)

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

    def get_state(self, state_name: STATE):
        state = self.db.get_state(state_name)
        if state_name in (STATE.SONGS_COL_SIZE, STATE.REPORT_COL_SIZE):
            table_name = HEADER(state_name.value.split("_")[0])
            state = map_db_rows_to_view_order(table_name=HEADER(table_name), data=state)
        return state

    def set_state(self, state_name: STATE, data: Any):
        if state_name in (STATE.SONGS_COL_SIZE, STATE.REPORT_COL_SIZE):
            table_name = HEADER(state_name.value.split("_")[0])
            data = map_ui_to_model_fields(data=data, table_name=HEADER(table_name))
        self.db.set_state(str(state_name.value), data)

    def close_connection(self):
        self.db.close()