from typing import Any, Dict, List, Type
from datetime import datetime, time

from sqlalchemy import Date, Time, DateTime, Integer, Float, Boolean

from .order_map import DEFAULT_CARD_VALUES, FIELD_MAPS
from ...enums import HEADER
from .models import Songs, Report, Base


class TableAdapter:
    MODEL_MAP: Dict[str, Type[Base]] = {
        HEADER.SONGS: Songs,
        HEADER.REPORT: Report
    }

    def __init__(self, table_name: str):
        self.header = HEADER(table_name.lower())
        self.model = self.MODEL_MAP[self.header]
        self.fields_map = FIELD_MAPS[self.header]
        self.columns = {col.name: col.type for col in self.model.__table__.columns}

    def to_db(self, ui_row: Dict[str, str], transform: bool = True) -> Dict[str, Any]:
        """
        Преобразует словарь из UI в словарь с полями модели ORM.
        """
        if transform:
            return {
                self.fields_map[k]: self._coerce(v, self.columns[self.fields_map[k]], self.fields_map[k])
                for k, v in ui_row.items()
                if k in self.fields_map
            }
        return {self.fields_map[k]: ui_row[k] for k in ui_row if k in self.fields_map}

    def to_view(self, db_row: Dict[str, Any], transform: bool = True) -> Dict[str, str | Any]:
        """
        Преобразует словарь ORM (из БД) в словарь с ключами для UI.
        """
        result = {}
        for ui_key in self._ui_headers():
            field = self.fields_map.get(ui_key)
            value = db_row.get(field)
            column_type = self.columns.get(field)
            if transform:
                result[ui_key] = self._stringify(value, column_type, field)
            else:
                result[ui_key] = value
        return result

    def to_table(self, db_rows: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Преобразует список ORM-строк в UI-таблицу (список списков).
        """
        headers = self._ui_headers()
        result = []
        for row in db_rows:
            line = []
            for ui_key in headers:
                field = self.fields_map.get(ui_key)
                value = row.get(field)
                column_type = self.columns.get(field)
                line.append(self._stringify(value, column_type, field))
            result.append(line)
        return result

    def _coerce(self, value: str, column_type: Any, field_name: str = "") -> Any:
        if value in ("", None):
            return None
        try:
            if isinstance(column_type, Date):
                return datetime.strptime(value, "%Y-%m-%d").date()

            elif isinstance(column_type, Time):
                if field_name == "duration" or len(value.split(":")) == 2:
                    m, s = map(int, value.split(":"))
                    return time(minute=m, second=s)
                return datetime.strptime(value, "%H:%M:%S").time()

            elif isinstance(column_type, DateTime):
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

            elif isinstance(column_type, Integer):
                return int(value)

            elif isinstance(column_type, Float):
                return float(value)

            elif isinstance(column_type, Boolean):
                return value.lower() in ("true", "1", "yes", "on")

        except Exception:
            print(f"[WARN] Failed to coerce field '{field_name}' with value '{value}' to {column_type}")
        return value

    def _stringify(self, value: Any, column_type: Any, field_name: str = "") -> str:
        if value is None:
            return ""
        if isinstance(column_type, Date):
            return value.strftime("%Y-%m-%d")
        elif isinstance(column_type, Time):
            if "duration" in field_name:
                return f"{value.minute}:{value.second:02}"
            return value.strftime("%H:%M:%S")
        elif isinstance(column_type, DateTime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    def _ui_headers(self) -> List[str]:
        return list(DEFAULT_CARD_VALUES[self.header].keys())

    def _to_report(self, db_rows: List[Dict[str, Any]], column_order: List[str]) -> List[
        List[Any]]:
        """
        Преобразует строки из БД в табличный формат по заданному порядку колонок.
        Поддерживает спец. колонку 'datetime' = объединение 'date' и 'time' в datetime.datetime.
        """
        result = []
        db_rows.sort(key=lambda x: (x.get("date"), x.get("id")))
        for row in db_rows:
            line = []
            for col in column_order:
                if col == "datetime":
                    date_val = row.get("date")
                    time_val = row.get("time")
                    line.append(datetime.combine(date_val, time_val))
                elif col == "play_count":
                    line.append(int(row.get(col)))
                else:
                    line.append(row.get(col))
            result.append(line)
        return result

    def to_month_report(self, db_rows: List[Dict[str, Any]]) -> List[List[Any]]:
        order = ["title", "composer", "lyricist", "play_count", "artist", "label"]
        return self._to_report(db_rows, order)

    def to_quarter_report(self, db_rows: List[Dict[str, Any]]) -> List[List[Any]]:
        order = ["program_name", "datetime", "title", "composer", "lyricist",
                 "play_duration", "play_count", "total_duration", "genre", "artist"]
        return self._to_report(db_rows, order)
