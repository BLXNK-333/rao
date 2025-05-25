from datetime import datetime
from typing import Dict, List

from ...enums import HEADER


DEFAULT_CARD_VALUES = {
    HEADER.SONGS: {
        "ID": "",
        "Исполнитель": "",
        "Название": "",
        "Время": "",
        "Композитор": "",
        "Автора текста": "",
        "Лэйбл": "ZAO Zalupa Prod."
    },
    HEADER.REPORT: {
        "ID": "",
        "Дата": datetime.today().strftime("%d-%m-%Y"),
        "Время": "8:20:00",
        "Исполнитель": "",
        "Название": "",
        "Длительность звучания": "",
        "Общий хронометраж": "",
        "Композитор": "",
        "Автор текста": "",
        "Передача": '"Будильник - шоу"',
        "Количество исполнений": "1",
        "Жанр": "песня",
        "Лэйбл": ""
    }
}


FIELD_MAPS = {
    HEADER.SONGS: {
        "ID": "id",
        "Исполнитель": "artist",
        "Название": "title",
        "Время": "duration",
        "Композитор": "composer",
        "Автора текста": "lyricist",
        "Лэйбл": "label"
    },
    HEADER.REPORT: {
        "ID": "id",
        "Дата": "date",
        "Время": "time",
        "Исполнитель": "artist",
        "Название": "title",
        "Длительность звучания": "play_duration",
        "Общий хронометраж": "total_duration",
        "Композитор": "composer",
        "Автор текста": "lyricist",
        "Передача": "program_name",
        "Количество исполнений": "play_count",
        "Жанр": "genre",
        "Лэйбл": "label"
    }
}


def get_headers(header: HEADER):
    return list(DEFAULT_CARD_VALUES.get(header).keys())


def map_ui_to_model_fields(table_name: str, data: Dict[str, str]) -> Dict[str, str]:
    """
    Преобразует пользовательские ключи словаря `data` (например, из UI)
    в имена полей ORM-модели.

    :param data: входной словарь с ключами из UI
    :param table_name: имя таблицы — 'songs' или 'report'
    :return: dict с ключами, соответствующими полям модели
    """
    table_key = HEADER(table_name.lower())
    field_map = FIELD_MAPS.get(table_key, {})
    return {
        field_map.get(key, key): value
        for key, value in data.items()
        if key in field_map
    }


def map_db_rows_to_view_order(table_name: str, data: Dict[str, str]) -> Dict[str, str]:
    """
    Преобразует dict с полями модели в dict с ключами из UI (в нужном порядке).

    :param table_name: имя таблицы — 'songs' или 'report'
    :param data: dict из БД (ключи — как в модели)
    :return: dict с ключами как в UI, в нужном порядке
    """
    table_key = HEADER(table_name.lower())
    headers = get_headers(table_key)
    field_map = FIELD_MAPS.get(table_key, {})

    # Построим reverse map: model field → UI key
    reverse_map = {v: k for k, v in field_map.items()}

    result = {}
    for ui_key in headers:
        model_key = field_map.get(ui_key)
        if model_key:
            result[ui_key] = data.get(model_key, "")
        else:
            result[ui_key] = ""
    return result


def convert_all_rows(table_name: str, rows: List[Dict[str, str]]) -> List[List[str]]:
    """
    Преобразует список строк из БД (каждая — dict с ключами как имена полей модели)
    в список списков значений в порядке, определённом DEFAULT_CARD_VALUES (для UI).

    :param table_name: имя таблицы 'songs' или 'report'
    :param rows: список dict с данными из БД
    :return: список списков значений в порядке отображения
    """
    table_key = HEADER(table_name.lower())
    headers = get_headers(table_key)
    field_map = FIELD_MAPS.get(table_key, {})
    desired_fields = [field_map.get(h) for h in headers]

    reordered_rows = []
    for row_dict in rows:
        new_row = [row_dict.get(field, "") for field in desired_fields]
        reordered_rows.append(new_row)

    return reordered_rows
