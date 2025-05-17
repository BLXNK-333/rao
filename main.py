from src.backend.service import BackendService
from src.frontend.viewUI import ViewUI
from src.frontend.songs import Table, DataTable, TablePanel, TableBuffer

from src.logging_config import set_logging_config
from src.eventbus import EventBus, TkDispatcher, QueueDispatcher
from src.enums import DispatcherType

from src.placeholder import SONG_HEADERS, SONGS_LIST


if __name__ == '__main__':
    backend = BackendService()
    view = ViewUI()

    queue = backend.msg_queue
    set_logging_config(queue=backend.msg_queue)
    view.terminal.term_logger.set_msq_queue(queue)

    # Тут палка в жопу, но временная, просто пока торчит
    SONGS_DICT = {row[0]: list(row) for row in SONGS_LIST}
    view.songs.buffer.original_data = SONGS_DICT

    view.terminal.term_panel.create_widget()
    view.terminal.term_logger.create_widget()
    view.songs.data_table.create_table(
        headers=SONG_HEADERS,
        data=SONGS_DICT.values(),
        stretchable_column_indices=[1, 2, 4, 5, 6]
    )

    tk_dispatcher = TkDispatcher(tk=view)
    table_dispatcher = QueueDispatcher()
    common_dispatcher = QueueDispatcher()

    EventBus.register_dispatcher(DispatcherType.TK, tk_dispatcher)
    EventBus.register_dispatcher(DispatcherType.SONG_TABLE, table_dispatcher)
    EventBus.register_dispatcher(DispatcherType.COMMON, common_dispatcher)

    EventBus.start()

    view.run()

    EventBus.stop_all_dispatchers()
