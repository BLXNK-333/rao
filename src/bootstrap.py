from .backend.service import BackendService
from .frontend.window import Window

from .backend.db.settings import get_headers, HEADERS

from .frontend.report import Report
from .frontend.export import Export
from .frontend.settings import Settings
from .frontend.terminal import Terminal
from .frontend.table.table import Table
from .frontend.table.card import CardManager
from .frontend.menu import TopMenu
from .frontend.icons.icon_map import Icons, ICON
from .frontend.style import UIStyles
from .frontend.bindings import apply_global_bindings

from .logging_config import set_logging_config
from .eventbus import EventBus, TkDispatcher, QueueDispatcher
from .enums import DispatcherType, HEADER, GROUP



def bootstrap():
    # TODO:
    #  1. Рефакторить логику инициализации, чтобы можно было просто собрать классы через
    #     интерфейсы, а лучше через конструкторы, через DI.
    #  2. Добавить сконфигурированный виджет таблицы на фрейм report.
    #  3. Сделать значения по умолчанию, и "тайтлинги" для заголовков.
    #  4. Написал логику экспорта, и генератор excel таблиц.
    #  5. Тестировать логику приложения.

    backend = BackendService()

    set_logging_config(queue=backend.msg_queue)
    all_songs_list = backend.sync_db.get_all_rows(HEADER.SONGS)
    all_report_list = ...

    window = Window()
    icons = Icons()
    UIStyles()
    apply_global_bindings(window)

    # Основные фреймы (все фреймы в 1 строке сетки)
    songs = Table(parent=window.content, group_id=GROUP.SONG_TABLE)
    songs.setup(
        headers=get_headers(HEADER.SONGS),
        data=all_songs_list,
        stretchable_column_indices=[1, 2, 4, 5, 6]
    )

    report = Report(parent=window.content)
    export = Export(parent=window.content)
    settings = Settings(parent=window.content)

    card_manager = CardManager(parent=window.content)
    card_manager.set_headers(HEADERS)

    terminal = Terminal(master=window)
    terminal.setup(state=window.terminal_state, msg_queue=backend.msg_queue)

    menu = TopMenu(
        master=window,
        on_tab_selected=window.switch_frame,
        on_term_selected=window.toggle_terminal,
        term_is_visible=window.terminal_visible,
        fix_size=False
    )

    # Добавляем обычные вкладки
    menu.add_tab("Songs", songs, image=icons[ICON.SONGS_LIST_24])
    menu.add_tab("Report", report, image=icons[ICON.REPORT_LIST_24])
    menu.add_tab("Export", export, image=icons[ICON.EXPORT_24])
    menu.add_tab("Settings", settings, image=icons[ICON.SETTINGS_24])

    window.switch_frame(songs)
    window.setup_layout(menu=menu, terminal=terminal)


    tk_dispatcher = TkDispatcher(tk=window)
    db_dispatcher = QueueDispatcher()
    table_dispatcher = QueueDispatcher()
    common_dispatcher = QueueDispatcher()

    EventBus.register_dispatcher(DispatcherType.TK, tk_dispatcher)
    EventBus.register_dispatcher(DispatcherType.DB, db_dispatcher)
    EventBus.register_dispatcher(DispatcherType.TABLE, table_dispatcher)
    EventBus.register_dispatcher(DispatcherType.COMMON, common_dispatcher)

    EventBus.start()
    window.run()

    EventBus.stop_all_dispatchers()
