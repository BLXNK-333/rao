from src.backend.service import BackendService
from src.frontend.viewUI import ViewUI

from src.logging_config import set_logging_config
from src.eventbus import EventBus, TkDispatcher, QueueDispatcher, Event, Subscriber
from src.enums import DispatcherType, HEADER, EventType, GROUP

from src.backend.db.settings import get_headers, HEADERS


class Zalupa:
    def __init__(self):
        handlers = [
            (EventType.VIEW.TABLE.DT.DELETE_CARDS, self.zalupa_print),
            (EventType.BACK.DB.CARD_VALUES, self.zalupa_print),
        ]
        for e, h in handlers:
            EventBus.subscribe(
                e,
                Subscriber(
                    callback=h,
                    route_by=DispatcherType.TABLE,
                    group_id=GROUP.REPORT_TABLE)
            )

    def zalupa_print(self, *args, **kwargs):
        print("Залупа сдесь была.")


if __name__ == '__main__':
    backend = BackendService()
    view = ViewUI()

    zzz = Zalupa()

    queue = backend.msg_queue
    set_logging_config(queue=backend.msg_queue)
    view.terminal.term_logger.set_msq_queue(queue)

    # Тут палка в жопу, но временная, просто пока торчит
    all_songs_list = backend.sync_db.get_all_rows(HEADER.SONGS)

    SONGS_DICT = {row[0]: list(row) for row in all_songs_list}
    view.songs.buffer.original_data = SONGS_DICT
    view.songs.buffer.sorted_keys = list(SONGS_DICT.keys())
    view.card_manager.set_headers(HEADERS)

    view.terminal.term_panel.create_widget()
    view.terminal.term_logger.create_widget()
    view.songs.data_table.create_table(
        headers=get_headers(HEADER.SONGS),
        data=all_songs_list,
        stretchable_column_indices=[1, 2, 4, 5, 6]
    )

    tk_dispatcher = TkDispatcher(tk=view)
    db_dispatcher = QueueDispatcher()
    table_dispatcher = QueueDispatcher()
    common_dispatcher = QueueDispatcher()

    EventBus.register_dispatcher(DispatcherType.TK, tk_dispatcher)
    EventBus.register_dispatcher(DispatcherType.DB, db_dispatcher)
    EventBus.register_dispatcher(DispatcherType.TABLE, table_dispatcher)
    EventBus.register_dispatcher(DispatcherType.COMMON, common_dispatcher)

    EventBus.start()

    view.run()

    EventBus.stop_all_dispatchers()
