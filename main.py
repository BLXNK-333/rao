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
    view.songs.data_table._headers = SONG_HEADERS
    view.songs.data_table._data = {row[0]: list(row) for row in SONGS_LIST}

    view.songs.buffer.original_data = SONGS_LIST
    view.songs.buffer.filtered_data = SONGS_LIST

    view.terminal.term_panel.create_widget()
    view.terminal.term_logger.create_widget()
    view.songs.data_table.create_widget()

    tk_dispatcher = TkDispatcher(tk=view)
    song_table_buffer_dispatcher = QueueDispatcher()
    common_dispatcher = QueueDispatcher()

    EventBus.register_dispatcher(DispatcherType.TK, tk_dispatcher)
    EventBus.register_dispatcher(DispatcherType.SONG_TABLE, song_table_buffer_dispatcher)
    EventBus.register_dispatcher(DispatcherType.COMMON, common_dispatcher)

    EventBus.start()

    view.run()

    EventBus.stop_all_dispatchers()
