from typing import Dict, List, Any, Union

from .database import Database
from .adapter import TableAdapter
from ...enums import EventType, DispatcherType, HEADER, GROUP, STATE
from ...eventbus import Event, Subscriber, EventBus
from ...entities import MonthReport, QuarterReport


class SyncDB:
    def __init__(self):
        self.db = Database()

        _song_adapter = TableAdapter(HEADER.SONGS)
        _report_adapter = TableAdapter(HEADER.REPORT)
        self.adapters: Dict[str, TableAdapter] = {
            HEADER.SONGS: _song_adapter,
            HEADER.REPORT: _report_adapter
        }
        self.subscribe()

    def subscribe(self):
        handlers = [
            (EventType.VIEW.UI.CLOSE_WINDOW, self.close_connection),
            (EventType.VIEW.TABLE.DT.EDIT_CARD, self.get_card),
            (EventType.VIEW.CARD.SAVE, self.save_card),
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self.delete_card),
            (EventType.VIEW.TABLE.DT.MANUAL_COL_SIZE, self.set_state),
            (EventType.VIEW.TABLE.DT.AUTO_COL_SIZE, self.set_state),
            (EventType.VIEW.EXPORT.PATH_CHANGED, self.set_state),
            (EventType.VIEW.EXPORT.GENERATE_REPORT, self.get_report)
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
        adapter = self.adapters.get(table_name)
        remapped_rows = adapter.to_table(all_rows)
        return remapped_rows

    def get_report(self, report: Union[MonthReport, QuarterReport]):
        adapter = self.adapters.get(HEADER.REPORT)
        if isinstance(report, MonthReport):
            db_rows = self.db.get_month_report(report.month, report.year)
            report.data = adapter.to_month_report(db_rows)
        elif isinstance(report, QuarterReport):
            db_rows = self.db.get_quarter_report(report.quarter, report.year)
            report.data = adapter.to_quarter_report(db_rows)
        else:
            pass

        EventBus.publish(
            Event(event_type=EventType.BACK.DB.REPORT),
            report
        )

    def get_card(self, table_name: str, card_id: str):
        db_row = self.db.get_card(table_name, card_id)
        adapter = self.adapters.get(table_name)
        remapped_row = adapter.to_view(db_row)
        EventBus.publish(
            Event(event_type=EventType.BACK.DB.CARD_DICT),
            table_name, remapped_row
        )

    def save_card(self, card_key: str, table_name: str, data: Dict[str, str]):
        card_id = data.get("ID")
        adapter = self.adapters.get(table_name)
        remapped_data = adapter.to_db(data)

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
            adapter = self.adapters.get(table_name)
            state = adapter.to_view(db_row=state, transform=False)
        return state

    def set_state(self, state_name: STATE, data: Any):
        if state_name in (STATE.SONGS_COL_SIZE, STATE.REPORT_COL_SIZE):
            table_name = HEADER(state_name.value.split("_")[0])
            adapter = self.adapters.get(table_name)
            data = adapter.to_db(ui_row=data, transform=False)
        self.db.set_state(str(state_name.value), data)

    def close_connection(self):
        self.db.close()