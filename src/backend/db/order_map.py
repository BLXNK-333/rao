from datetime import datetime

from ...enums import HEADER


DEFAULT_CARD_VALUES = {
    HEADER.SONGS: {
        "ID": "",
        "Исполнитель": "",
        "Название": "",
        "Время": "",
        "Композитор": "",
        "Автор текста": "",
        "Лэйбл": ""
    },
    HEADER.REPORT: {
        "ID": "",
        "Дата": datetime.today().strftime("%Y-%m-%d"),
        "Время": "8:20:00",
        "Исполнитель": "",
        "Название": "",
        "Длительность звучания": "",
        "Общий хронометраж": "",
        "Композитор": "",
        "Автор текста": "",
        "Передача": "Будильник - шоу",
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
        "Автор текста": "lyricist",
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


FIELD_MAPS_REVERSED = {
    key: {v: k for k, v in field_map.items()}
    for key, field_map in FIELD_MAPS.items()
}


def get_headers(header: HEADER):
    return list(DEFAULT_CARD_VALUES.get(header).keys())
