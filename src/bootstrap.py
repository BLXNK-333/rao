from .backend.service import BackendService
from .frontend.window import Window

from .backend.db.order_map import DEFAULT_CARD_VALUES, FIELD_MAPS

from .frontend.frames import SongsTable, Report, Export, Settings
from .frontend.widgets import Terminal, Table, CardManager, TopMenu, TooltipManager
from .frontend.icons.icon_map import Icons, ICON
from .frontend.style import UIStyles
from .frontend.bindings import apply_global_bindings

from .logging_config import set_logging_config
from .eventbus import EventBus, TkDispatcher, QueueDispatcher
from .enums import DispatcherType, HEADER, GROUP, STATE, ConfigKey


def bootstrap():
    # -------------------------------
    # Backend initialization
    # -------------------------------
    backend = BackendService()
    set_logging_config(queue=backend.msg_queue)

    songs_table_cols_state = backend.sync_db.get_state(STATE.SONGS_COL_SIZE)
    report_table_cols_state = backend.sync_db.get_state(STATE.REPORT_COL_SIZE)
    monthly_path_state = backend.sync_db.get_state(STATE.MONTHLY_PATH)
    quarterly_path_state = backend.sync_db.get_state(STATE.QUARTERLY_PATH)
    songs_table_sort_state = backend.sync_db.get_state(STATE.SONGS_SORT)
    report_table_sort_state = backend.sync_db.get_state(STATE.REPORT_SORT)

    settings = backend.sync_db.get_settings()

    # -------------------------------
    # UI initialization
    # -------------------------------
    window = Window(
        terminal_visible=settings.get(ConfigKey.SHOW_TERMINAL),
        terminal_state=settings.get(ConfigKey.TERMINAL_SIZE)
    )
    icons = Icons()
    UIStyles(window)
    apply_global_bindings(window)

    # -------------------------------
    # Main UI frames creation
    # -------------------------------
    tooltip_manager = TooltipManager(master=window)

    songs = SongsTable(
        parent=window.content,
        group_id=GROUP.SONGS_TABLE,
        header_map=FIELD_MAPS.get(HEADER.SONGS),
        data=backend.sync_db.get_all_rows(HEADER.SONGS),
        stretchable_column_indices=[1, 2, 4, 5, 6],
        enable_tooltips=False,
        default_report_values=DEFAULT_CARD_VALUES[HEADER.REPORT],
        show_table_end=False,
        prev_cols_state=songs_table_cols_state,
        sort_key_state=songs_table_sort_state
    )

    report = Table(
        parent=window.content,
        group_id=GROUP.REPORT_TABLE,
        header_map=FIELD_MAPS.get(HEADER.REPORT),
        data=backend.sync_db.get_all_rows(HEADER.REPORT),
        stretchable_column_indices=[3, 4, 7, 8, 12],
        enable_tooltips=True,
        show_table_end=True,
        prev_cols_state=report_table_cols_state,
        sort_key_state=report_table_sort_state
    )
    export = Export(
        parent=window.content,
        monthly_path=monthly_path_state,
        quarterly_path=quarterly_path_state
    )
    settings = Settings(
        parent=window.content,
        settings=settings,
        version="1.1.0",
        github_url="https://github.com/BLXNK-333/rao"
    )

    card_manager = CardManager(
        parent=window.content,
        default_card_values=DEFAULT_CARD_VALUES
    )

    terminal = Terminal(
        master=window,
        state=window.terminal_state,
        msg_queue=backend.msg_queue
    )

    menu = TopMenu(
        master=window,
        on_tab_selected=window.switch_frame,
        on_term_selected=window.toggle_terminal,
        term_is_visible=window.terminal_visible,
        fix_size=False
    )

    # -------------------------------
    # Menu tabs setup
    # -------------------------------
    menu.add_tab("Песни", songs, image=icons[ICON.SONGS_LIST_24])
    menu.add_tab("Отчет", report, image=icons[ICON.REPORT_LIST_24])
    menu.add_tab("Экспорт", export, image=icons[ICON.EXPORT_24])
    menu.add_tab("Настройки", settings, image=icons[ICON.SETTINGS_24])

    # -------------------------------
    # Window initial layout
    # -------------------------------
    window.switch_frame(songs)
    window.setup_layout(menu=menu, terminal=terminal, card_manager=card_manager)

    # -------------------------------
    # EventBus and dispatchers setup
    # -------------------------------
    tk_dispatcher = TkDispatcher(tk=window)
    db_dispatcher = QueueDispatcher()
    table_dispatcher = QueueDispatcher()
    common_dispatcher = QueueDispatcher()

    EventBus.register_dispatcher(DispatcherType.TK, tk_dispatcher)
    EventBus.register_dispatcher(DispatcherType.DB, db_dispatcher)
    EventBus.register_dispatcher(DispatcherType.TABLE, table_dispatcher)
    EventBus.register_dispatcher(DispatcherType.COMMON, common_dispatcher)

    EventBus.start()

    # -------------------------------
    # Start main application loop
    # -------------------------------
    window.run()

    # -------------------------------
    # Cleanup on exit
    # -------------------------------
    EventBus.stop_all_dispatchers()
