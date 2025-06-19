import re
from datetime import datetime
from typing import Dict

from .order_map import FIELD_MAPS
from ...eventbus import EventBus, Event
from ...enums import EventType


class DataValidator:
    TIME_REGEX = re.compile(r"^(\d{1,2}:)?\d{1,2}:\d{2}$")  # H:MM:SS или MM:SS

    def __init__(self):
        self.field_maps = FIELD_MAPS

    def validate(self, card_key: str, table_name: str, data: Dict[str, str]) -> bool:
        if table_name == "songs":
            validated = self._validate_songs(table_name, data)
        else:
            validated = self._validate_report(table_name, data)

        EventBus.publish(Event(
            event_type=EventType.BACK.DB.VALIDATION
        ), card_key, validated)

        return all(validated.values())

    def _validate_songs(self, table_name: str, data: Dict[str, str]) -> Dict[str, bool]:
        validated = {}
        for view_key, val in data.items():
            db_key = self.field_maps[table_name].get(view_key)

            if db_key in {"artist", "title"}:
                validated[view_key] = bool(val.strip())
            elif db_key == "duration":
                validated[view_key] = self._is_time_format(val)
            else:
                validated[view_key] = True

        return validated

    def _validate_report(self, table_name: str, data: Dict[str, str]) -> Dict[str, bool]:
        validated = {}
        for view_key, val in data.items():
            db_key = self.field_maps[table_name].get(view_key)

            if db_key in {"artist", "title"}:
                validated[view_key] = bool(val.strip())

            elif db_key in {"time", "play_duration", "total_duration"}:
                validated[view_key] = self._is_time_format(val)

            elif db_key == "date":
                validated[view_key] = self._is_date_format(val)

            elif db_key == "play_count":
                validated[view_key] = val.isdigit()

            else:
                validated[view_key] = True

        return validated

    def _is_time_format(self, value: str) -> bool:
        """Допускается HH:MM:SS или MM:SS или H:MM"""
        if not isinstance(value, str):
            return False

        try:
            value = value.replace('.', ':').replace(',', ':')
            # Попробуем разные форматы
            if value.count(":") == 2:
                datetime.strptime(value, "%H:%M:%S")
            elif value.count(":") == 1:
                datetime.strptime(value, "%M:%S")
            else:
                return False
            return True
        except ValueError:
            return False

    def _is_date_format(self, value: str) -> bool:
        """Ожидается формат YYYY-MM-DD"""
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
