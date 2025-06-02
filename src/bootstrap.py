from .backend.service import BackendService
from .frontend.window import Window

from .backend.db.order_map import DEFAULT_CARD_VALUES, get_headers

from .frontend.frames import SongsTable, Report, Export, Settings
from .frontend.widgets import Terminal, Table, CardManager, TopMenu
from .frontend.icons.icon_map import Icons, ICON
from .frontend.style import UIStyles
from .frontend.bindings import apply_global_bindings

from .logging_config import set_logging_config
from .eventbus import EventBus, TkDispatcher, QueueDispatcher
from .enums import DispatcherType, HEADER, GROUP, STATE


def bootstrap():
    # TODO:
    #  + 1. Рефакторить логику инициализации, чтобы можно было просто собрать классы через
    #     интерфейсы, а лучше через конструкторы, через DI.
    #  + 2. Добавить сконфигурированный виджет таблицы на фрейм report.
    #  + 3. Сделать значения по умолчанию, и "тултипы" для заголовков
    #      (насчет тултипов, не ясно пока нужны ли они).
    #  4. Написал логику экспорта, и генератор excel таблиц.
    #  5. Тестировать логику приложения.

    # TODO:
    #  + 1. Узкое место слишком тяжелый метод, нужно переделать логику.
    #   Перенести вычисление в буфер таблицы и считать, написать там как-то, а сюда
    #   отправлять событие с обновленными ширинами если нужно. Этот метод упростить
    #   до сеттера, или избавиться.
    #  + 2. Убрать лишние биндинги. Проверить метод _resize_columns, там 2 раза меняется
    #   ширина, подумать как оптимизировать.
    #  + 3. Добавить логику которая будет добавлять состояние ширин столбцов в таблицу
    #   состояний в бд.
    #  + 4. Понять почему не работает ресайз когда в таблице нет записей. Может должен по
    #   заголовкам брать если пусто в размерах.
    #  - 5. Эта логика все время делает одно и тоже (_adjust_column_widths), и это нужно кэшировать
    #   (пока размеры считаются только на старте, и нет логики обновлений self.estimated_column_widths).
    #  - 6. Написать виджет настроек. И добавить таблицу настроек в бд.
    #  - 7. Проверить функцию-ключ сортировки в буфере таблицы
    #  - 8. Привести логи к одному унифицированному виду, и сделать на 1 языке (ru, тут будет)
    #  - 9. Добавить bind на Del для удаления элементов из таблицы
    #  - 10. Добавить логику проверки открытых карточек перед закрытием, сохранять или нет.
    #  ? 11. Исправить баг с переключением сортировки, когда не работает дебаунс, а просто блокирует.
    #  - 12. Добавить слой валидации введенных пользователем данных, перед адаптером
    #  и логикой базы, понять что возвращать если не прошел валидацию. Или может просто
    #  поменять логику функции обновления добавления строки, так как DB сама валидирует
    #  и не даст сохранить, чтобы во view приходило обновление только после сохранения в базу данных
    #  - 13. Написать скрипт для легкого экспорта из excel файлов и добавления в базу.
    #  - 14. Установить ВМ с Windows 7 и адаптировать под версию python 3.8.xx, проверить
    #  какие зависимости потребует, и написать док как установить на шиндоус.
    #  - 15. Исправить баг с форматом в экспортируемом отчете, сейчас там где "play_count",
    #  текст, должно быть число.
    #  - 16. Нужно чтобы у отчетов был консистентный вид, поэтому перед записью в файл,
    #  нужно отсортировать таблицу, которая приходит в builder, по колонке "datetime",
    #  такая появляется после выхода с адаптера. (и возможно по id но он не передается,
    #  поэтому не факт что это нужно)
    #  - 17. Нужно сохранять состояние сортировки из таблиц, и передавать в базу
    #  при обновлении. На старте соответственно применять сортировку.

    # -------------------------------
    # Backend initialization
    # -------------------------------
    backend = BackendService()
    set_logging_config(queue=backend.msg_queue)
    all_songs_list = backend.sync_db.get_all_rows(HEADER.SONGS)
    all_report_list = backend.sync_db.get_all_rows(HEADER.REPORT)

    songs_table_cols_state = backend.sync_db.get_state(STATE.SONGS_COL_SIZE)
    report_table_cols_state = backend.sync_db.get_state(STATE.REPORT_COL_SIZE)
    monthly_path_state = backend.sync_db.get_state(STATE.MONTHLY_PATH)
    quarterly_path_state = backend.sync_db.get_state(STATE.QUARTERLY_PATH)

    # -------------------------------
    # UI initialization
    # -------------------------------
    window = Window()
    icons = Icons()
    UIStyles()
    apply_global_bindings(window)

    # -------------------------------
    # Main UI frames creation
    # -------------------------------
    songs = SongsTable(
        parent=window.content,
        group_id=GROUP.SONGS_TABLE,
        headers=get_headers(HEADER.SONGS),
        data=all_songs_list,
        stretchable_column_indices=[1, 2, 4, 5, 6],
        prev_cols_state=songs_table_cols_state,
        enable_tooltips=False,
        default_report_values=DEFAULT_CARD_VALUES[HEADER.REPORT],
        scroll_to_the_bottom=False
    )

    report = Table(
        parent=window.content,
        group_id=GROUP.REPORT_TABLE,
        headers=get_headers(HEADER.REPORT),
        data=all_report_list,
        stretchable_column_indices=[3, 4, 7, 8, 12],
        prev_cols_state=report_table_cols_state,
        enable_tooltips=True,
        scroll_to_the_bottom=True
    )
    export = Export(
        parent=window.content,
        monthly_path=monthly_path_state,
        quarterly_path=quarterly_path_state
    )
    settings = Settings(parent=window.content)

    card_manager = CardManager(parent=window.content)
    card_manager.set_default_card_values(DEFAULT_CARD_VALUES)

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
    window.setup_layout(menu=menu, terminal=terminal)

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
