from enum import Enum


class ICON(str, Enum):
    ADD_CARD_24 = "add_card_24"
    CLONE_CARD_24 = "clone_card_24"
    EDIT_CARD_24 = "edit_card_24"
    DELETE_CARD_24 = "delete_card_24"
    AUTO_SIZE_ON_24 = "auto_size_on_24"
    AUTO_SIZE_OFF_24 = "auto_size_off_24"
    ERASER_24 = "eraser_24"

    SONGS_LIST_24 = "songs_list_24"
    REPORT_LIST_24 = "report_list_24"
    EXPORT_24 = "export_24"
    SETTINGS_24 = "settings_24"

    TERMINAL_LIGHT_24 = "terminal_light_24"
    TERMINAL_LIGHT_DOT_24 = "terminal_light_dot_24"
    TERMINAL_DARK_24 = "terminal_dark_24"
    TERMINAL_DARK_DOT_24 = "terminal_dark_dot_24"

    STOP_RED_16 = "stop_red_16"
    STOP_GRAY_16 = "stop_gray_16"
    CLEAR_16 = "clear_16"
    TERM_SMALL_DARK_16 = "term_small_dark_16"
    TERM_SMALL_LIGHT_16 = "term_small_light_16"
    TERM_MEDIUM_DARK_16 = "term_medium_dark_16"
    TERM_MEDIUM_LIGHT_16 = "term_medium_light_16"
    TERM_LARGE_DARK_16 = "term_large_dark_16"
    TERM_LARGE_LIGHT_16 = "term_large_light_16"
    CLOSE_16 = "close_16"

    FOLDER_16 = "folder_16"
    PIN_ON_24 = "pin_on_24"
    PIN_OFF_24 = "pin_off_24"
    EYE_24 = "eye_24"
    HIDDEN_24 = "hidden_24"

    VERSION_24 = "version_24",
    CODE_24 = "code_24"


class TERM(str, Enum):
    """Обозначают размеры окна терминала"""
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class DispatcherType(str, Enum):
    TK = "TK"
    DB = "DB"
    TABLE = "TABLE"
    COMMON = "COMMON"


class GROUP(str, Enum):
    SONGS_TABLE = "songs"
    REPORT_TABLE = "report"


class HEADER(str, Enum):
    SONGS = "songs"
    REPORT = "report"


class STATE(str, Enum):
    SONGS_COL_SIZE = "songs_col_size"
    REPORT_COL_SIZE = "report_col_size"
    MONTHLY_PATH = "monthly_path"
    QUARTERLY_PATH = "quarterly_path"
    SONGS_SORT = "songs_sort"
    REPORT_SORT = "report_sort"


class ConfigKey(str, Enum):
    SHOW_TERMINAL = "SHOW_TERMINAL"
    TERMINAL_SIZE = "TERMINAL_SIZE"
    CARD_TRANSPARENCY = "CARD_TRANSPARENCY"
    CARD_PIN = "CARD_PIN"
    SONG_TOOLTIPS = "SONG_TOOLTIPS"
    REPORT_TOOLTIPS = "REPORT_TOOLTIPS"
    # etc.


class EventType:
    class BACK:
        class SIG:
            # Сигнал для вью, что задача начала выполняться.
            TASK_RUNNING = "BACK.SIG.TASK_RUNNING"
            # Сигнал для backend фасада, что задача выполнена
            TASK_COMPLETE = "BACK.SIG.TASK_COMPLETE"
            # Сигнал для вью, что нет активных задач.
            NO_ACTIVE_TASK = "BACK.SIG.NO_ACTIVE_TASK"

        class DB:
            # События связанные с рассылкой данных.
            # SETTINGS = "BACK.DB.SETTINGS"
            # DEFAULT_SETTINGS = "BACK.DB.DEFAULT_SETTINGS"
            TABLE = "BACK.DB.TABLE"
            CARD_VALUES = "BACK.DB.CARD_VALUES"
            CARD_ID = "BACK.DB.CARD_ID"
            CARD_DICT = "BACK.DB.CARD_DICT"
            REPORT = "BACK.DB.REPORT"
            VALIDATION = "BACK.DB.VALIDATION"

        class EXPORT:
            MESSAGE = "BACK.EXPORT.MESSAGE"

        class LOGGER:
            EMITTED = "BACK.LOGGER.EMITTED"


    class VIEW:
        # View signals
        class TERM:
            CLEAR = "VIEW.TERM.CLEAR"
            CLOSE = "VIEW.TERM.CLOSE"
            STOP = "VIEW.TERM.STOP"
            SMALL = "VIEW.TERM.SMALL"
            MEDIUM = "VIEW.TERM.MEDIUM"
            LARGE = "VIEW.TERM.LARGE"

        class TABLE:
            class PANEL:
                ADD_CARD = "VIEW.TABLE.PANEL.ADD_CARD"
                CLONE_CARD = "VIEW.TABLE.PANEL.CLONE_CARD"
                EDIT_CARD = "VIEW.TABLE.PANEL.EDIT_CARD"
                DELETE_CARD = "VIEW.TABLE.PANEL.DELETE_CARD"
                SEARCH_VALUE = "VIEW.TABLE.PANEL.SEARCH_VALUE"
                AUTO_SIZE = "VIEW.TABLE.PANEL.AUTO_SIZE"

            class DT:
                EDIT_CARD = "VIEW.TABLE.DT.EDIT_CARD"
                DELETE_CARDS = "VIEW.TABLE.DT.DELETE_CARDS"
                SORT_CHANGED = "VIEW.TABLE.DT.SORT_CHANGED"
                MANUAL_COL_SIZE = "VIEW.TABLE.DT.MANUAL_COL_SIZE"
                AUTO_COL_SIZE = "VIEW.TABLE.DT.AUTO_COL_SIZE",
                CLONE_ITEM = "VIEW.TABLE.DT.CLONE_ITEM",

            class BUFFER:
                FILTERED_TABLE = "VIEW.TABLE.FILTERED_TABLE"
                CARD_UPDATED = "VIEW.TABLE.CARD_UPDATED"
                INVISIBLE_ID = "VIEW.TABLE.INVISIBLE_ID"

            HEADER_TOOLTIPS_STATE = "VIEW.TABLE.HEADER_TOOLTIPS_STATE"

        class SONGS_TABLE:
            ADD_TO_REPORT = "VIEW.SONGS_TABLE.ADD_TO_REPORT"

        class CARD:
            SAVE = "VIEW.CARD.SAVE"
            DESTROY = "VIEW.CARD.DESTROY"

        class EXPORT:
            GENERATE_REPORT = "VIEW.CARD.GENERATE_REPORT"
            PATH_CHANGED = "VIEW.CARD.PATH_CHANGED"

        class SETTINGS:
            ON_CHANGE = "VIEW.SETTING.ON_CHANGE"
            CARD_TRANSPARENCY = "VIEW.SETTING.CARD_TRANSPARENCY"
            CARD_PIN = "VIEW.SETTING.CARD_PIN"
            HEADER_TOOLTIPS_STATE = "VIEW.SETTING.HEADER_TOOLTIPS_STATE"

        class UI:
            CLOSE_WINDOW = "VIEW.UI.CLOSE_WINDOW"

    # PLACEHOLDER
    FAKE_EVENT = "FAKE_EVENT"
