from enum import StrEnum


class ICON(StrEnum):
    ADD_CARD_24 = "add_card_24"
    EDIT_CARD_24 = "edit_card_24"
    DELETE_CARD_24 = "delete_card_24"

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


class CONFIGKEYS(StrEnum):
    pass


class TERM(StrEnum):
    """Обозначают размеры окна терминала"""
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class DispatcherType(StrEnum):
    TK = "TK"
    DB = "DB"
    SONG_TABLE = "SONG_TABLE"
    REPORT_TABLE = "REPORT_TABLE"
    COMMON = "COMMON"


class GROUP(StrEnum):
    SONG_TABLE = "songs"
    REPORT_TABLE = "report"


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
            SETTINGS = "BACK.DB.SETTINGS"
            DEFAULT_SETTINGS = "BACK.DB.DEFAULT_SETTINGS"
            TABLE = "BACK.DB.TABLE"
            CARD_UPDATED = "BACK.DB.CARD_UPDATED"


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
                EDIT_CARD = "VIEW.TABLE.PANEL.EDIT_CARD"
                DELETE_CARD = "VIEW.TABLE.PANEL.DELETE_CARD"
                SEARCH_VALUE = "VIEW.TABLE.PANEL.SEARCH_VALUE"

            class DT:
                EDIT_CARD = "VIEW.TABLE.DT.EDIT_CARD"
                DELETE_CARDS = "VIEW.TABLE.DT.DELETE_CARDS"

            class BUFFER:
                FILTERED_TABLE = "VIEW.TABLE.FILTERED_TABLE"
                CARD_UPDATED = "VIEW.TABLE.CARD_UPDATED"

            class CARD:
                SAVE = "VIEW.TABLE.SAVE_CARD"
                DESTROY = "VIEW.TABLE.CLOSE_CARD"

        class SETTINGS:
            class CLICK:
                SAVE = "VIEW.SETTINGS.CLICK.SAVE"
                RESET = "VIEW.SETTINGS.CLICK.RESET"
                CANCEL = "VIEW.SETTINGS.CLICK.CANCEL"

            class DATA:
                PAYLOAD = "VIEW.SETTINGS.DATA.PAYLOAD"

        class UI:
            CLOSE_WINDOW = "VIEW.UI.CLOSE_WINDOW"

    # PLACEHOLDER
    FAKE_EVENT = "FAKE_EVENT"
