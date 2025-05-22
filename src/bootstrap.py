from src.backend.service import BackendService
from src.frontend.viewUI import ViewUI

from src.logging_config import set_logging_config
from src.eventbus import EventBus, TkDispatcher, QueueDispatcher
from src.enums import DispatcherType, HEADER

from src.backend.db.settings import get_headers, HEADERS


def bootstrap():
    # TODO:
    #  1. Рефакторить логику инициализации, чтобы можно было просто собрать классы через
    #     интерфейсы, а лучше через конструкторы, через DI.
    #  2. Добавить сконфигурированный виджет таблицы на фрейм report.
    #  3. Сделать значения по умолчанию, и "тайтлинги" для заголовков.
    #  4. Написал логику экспорта, и генератор excel таблиц.
    #  5. Тестировать логику приложения.

    backend = BackendService()
    view = ViewUI()

    set_logging_config(queue=backend.msg_queue)
    view.terminal.setup(state=view.terminal_state, msg_queue=backend.msg_queue)

    view.card_manager.set_headers(HEADERS)

    all_songs_list = backend.sync_db.get_all_rows(HEADER.SONGS)
    all_report_list = ...

    view.songs.setup(
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
