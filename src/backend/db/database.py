from typing import List, Dict, Optional, Type, Any
from datetime import datetime
import logging
from pathlib import Path
import traceback

from sqlalchemy.types import Date, Time, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, State, Songs, Report
from .base import DB_PATH, Engine, SessionFactory


class Database:
    model_map: Dict[str, Type[Base]] = {
        "songs": Songs,
        "report": Report,
    }

    def __init__(self) -> None:
        """
        Управляющий класс базы данных синхронизации (ORM).
        """
        self._logger = logging.getLogger(__name__)
        self.db_path: Path = DB_PATH
        self.engine = Engine
        self.session: Session = SessionFactory()
        self._initialization()

    def _initialization(self):
        try:
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            self._logger.error(f"Database error during initialization: {e}")
            self._logger.debug(traceback.format_exc())
            self.close()

    def get_all_rows(self, table_name: str) -> List[Dict[str, str]]:
        """
        Возвращает все строки из таблицы как список словарей:
        [{field_name: value, ...}, ...] с корректной сериализацией значений.
        """
        model = self.model_map.get(table_name.lower())
        if not model:
            self._logger.error(f"Invalid table name: {table_name}")
            return []

        try:
            records = self.session.query(model).all()
            rows = []

            for record in records:
                row_dict = {}
                for col in model.__table__.columns:
                    raw_value = getattr(record, col.name)
                    column_type = col.type
                    stringified = self.stringify_column_value(raw_value, column_type)
                    row_dict[col.name] = stringified
                rows.append(row_dict)

            return rows

        except SQLAlchemyError as e:
            self._logger.error(f"Database error in get_all_rows('{table_name}'): {e}")
            self._logger.debug(traceback.format_exc())
            return []

    def get_month_report(self, month: int, year: int):
        pass

    def get_quarter_report(self, quarter: int, year: int):
        pass

    def get_card(self, table_name: str, card_id: str) -> Optional[Dict[str, str]]:
        """
        Получает одну запись по ID из указанной таблицы ('songs' или 'report')
        и возвращает как словарь: {field_name: value, ...} с корректной сериализацией.

        :param table_name: имя таблицы ('songs' или 'report')
        :param card_id: строковое значение ID записи
        :return: словарь значений полей или None, если запись не найдена
        """
        model = self.model_map.get(table_name.lower())
        if not model:
            self._logger.error(f"Invalid table name in get_card: {table_name}")
            return None

        try:
            record = self.session.get(model, int(card_id))
            if not record:
                self._logger.warning(
                    f"Record with ID {card_id} not found in {table_name}")
                return None

            result = {}
            for col in model.__table__.columns:
                raw_value = getattr(record, col.name)
                column_type = col.type
                stringified = self.stringify_column_value(raw_value, column_type)
                result[col.name] = stringified
            return result

        except SQLAlchemyError as e:
            self._logger.error(
                f"Database error in get_card('{table_name}', '{card_id}'): {e}")
            self._logger.debug(traceback.format_exc())
            return None

    def add_card(self, table_name: str, payload: dict) -> Optional[str]:
        """
        Добавляет новую запись в указанную таблицу (songs или report).
        Преобразует строковые значения в нужные типы, согласно схеме таблицы.
        """
        model_cls = self.model_map.get(table_name.lower())
        if not model_cls:
            self._logger.error(f"add_card: неизвестная таблица '{table_name}'")
            return None

        try:
            payload.pop("ID", None)
            payload.pop("id", None)

            converted_payload = {}

            for column in model_cls.__table__.columns:
                col_name = column.name
                if col_name in payload:
                    raw_value = payload[col_name]
                    column_type = column.type
                    converted_payload[col_name] = self.coerce_column_value(raw_value,
                                                                           column_type)

            new_instance = model_cls(**converted_payload)
            self.session.add(new_instance)
            self.session.commit()

            card_id = str(new_instance.id)
            self._logger.debug(
                f"{model_cls.__name__} (ID: {card_id}) добавлена в таблицу '{table_name}'")
            return card_id

        except Exception as e:
            self._logger.error(
                f"Ошибка при добавлении записи в таблицу '{table_name}': {e}")
            self._logger.debug(traceback.format_exc())
            self.session.rollback()
            return None

    def update_card(self, card_id: str, table_name: str, payload: dict) -> None:
        """
        Обновляет запись в указанной таблице по ID.
        Преобразует типы значений согласно схеме таблицы.

        :param card_id: ID записи.
        :param table_name: Название таблицы ('songs' или 'report').
        :param payload: Обновлённые данные.
        """
        model_cls = self.model_map.get(table_name.lower())
        if not model_cls:
            self._logger.error(f"update_card: неизвестная таблица '{table_name}'")
            return

        try:
            record = self.session.get(model_cls, int(card_id))
            if not record:
                self._logger.warning(f"{model_cls.__name__} с ID {card_id} не найдена.")
                return

            for column in model_cls.__table__.columns:
                col_name = column.name
                if col_name in payload:
                    raw_value = payload[col_name]
                    column_type = column.type
                    coerced_value = self.coerce_column_value(raw_value, column_type)
                    setattr(record, col_name, coerced_value)

            self.session.commit()
            self._logger.debug(
                f"{model_cls.__name__} (ID: {card_id}) обновлена в таблице '{table_name}'")

        except Exception as e:
            self._logger.error(
                f"Ошибка при обновлении записи ID={card_id} в таблице '{table_name}': {e}")
            self._logger.debug(traceback.format_exc())
            self.session.rollback()

    def delete_card(self, deleted_ids: List[str], table_name: str) -> None:
        """
        Deletes cards from the specified table by their IDs.

        :param deleted_ids: List of string IDs to delete.
        :param table_name: Name of the table ('songs' or 'report').
        """
        model_cls = self.model_map.get(table_name.lower())
        if not model_cls:
            self._logger.error(f"delete_card: неизвестная таблица '{table_name}'")
            return

        try:
            count = (
                self.session.query(model_cls)
                .filter(model_cls.id.in_(map(int, deleted_ids)))
                .delete(synchronize_session=False)
            )
            self.session.commit()
            self._logger.debug(
                f"Удалено {count} карточек из таблицы '{table_name}' с ID: {deleted_ids}")

        except Exception as e:
            self._logger.error(f"Ошибка при удалении карточек из таблицы '{table_name}': {e}")
            self._logger.debug(traceback.format_exc())
            self.session.rollback()

    def get_state(self, key: str) -> Optional[Any]:
        """
        Получает значение состояния по ключу.

        :param key: строковый ключ состояния
        :return: значение (dict / list / str / bool / int / float), если найдено; иначе None
        """
        try:
            record = self.session.get(State, key)
            return record.value if record else None
        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка при получении состояния по ключу '{key}': {e}")
            self._logger.debug(traceback.format_exc())
            return None

    def set_state(self, key: str, value) -> None:
        """
        Устанавливает или обновляет состояние по ключу.

        :param key: строковый ключ
        :param value: значение (должно быть сериализуемо в JSON)
        """
        try:
            existing = self.session.get(State, key)
            if existing:
                existing.value = value
            else:
                self.session.add(State(key=key, value=value))
            self.session.commit()
            # self._logger.debug(f"Обновлено состояние: '{key}', с значениями {value}")
        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка при установке состояния '{key}': {e}")
            self._logger.debug(traceback.format_exc())
            self.session.rollback()

    def close(self):
        """
        Закрывает соединение.
        """
        self.session.close()

    @staticmethod
    def coerce_column_value(value: str, column_type) -> Any:
        if value in ("", None):
            return None

        try:
            if isinstance(column_type, Date):
                return datetime.strptime(value, "%Y-%m-%d").date()
            elif isinstance(column_type, Time):
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
            pass

        return value

    @staticmethod
    def stringify_column_value(value: Any, column_type) -> str:
        if value is None:
            return ""

        if isinstance(column_type, Date):
            return value.strftime("%Y-%m-%d")
        elif isinstance(column_type, Time):
            return value.strftime("%M:%S")
        elif isinstance(column_type, DateTime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)
