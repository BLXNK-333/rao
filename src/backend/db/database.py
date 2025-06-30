from typing import List, Dict, Optional, Type, Any
import json
import logging
import datetime
from pathlib import Path
import traceback

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, State, Songs, Report, Settings
from .base import DB_PATH, Engine, SessionFactory
from ...enums import HEADER


class Database:
    model_map: Dict[str, Type[Base]] = {
        HEADER.SONGS.value: Songs,
        HEADER.REPORT.value: Report,
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
            self._logger.error(f"Ошибка базы данных во время инициализации: {e}")
            self._logger.debug(traceback.format_exc())
            self.close()

    def get_all_rows(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Возвращает все строки из таблицы как список словарей:
        [{field_name: value, ...}, ...]
        """
        model = self.model_map.get(table_name.lower())
        if not model:
            self._logger.error(f"Недопустимое имя таблицы: {table_name}")
            return []

        try:
            records = self.session.query(model).all()
            rows = []
            for record in records:
                row_dict = {}
                for col in model.__table__.columns:
                    value = getattr(record, col.name)
                    row_dict[col.name] = value
                rows.append(row_dict)
            return rows
        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка базы данных в get_all_rows('{table_name}'): {e}")
            self._logger.debug(traceback.format_exc())
            return []

    def get_month_report(self, month: int, year: int) -> List[Dict[str, Any]]:
        try:
            start_date = datetime.date(year, month, 1)
            # Конец месяца: если декабрь — следующий январь, иначе следующий месяц
            if month == 12:
                end_date = datetime.date(year + 1, 1, 1)
            else:
                end_date = datetime.date(year, month + 1, 1)

            query = (
                self.session.query(Report)
                .filter(Report.date >= start_date, Report.date < end_date)
                .all()
            )

            rows = []
            for record in query:
                row_dict = {}
                for col in Report.__table__.columns:
                    value = getattr(record, col.name)
                    row_dict[col.name] = value
                rows.append(row_dict)
            return rows

        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка в get_month_report({month=}, {year=}): {e}")
            self._logger.debug(traceback.format_exc())
            return []

    def get_quarter_report(self, quarter: int, year: int) -> List[Dict[str, Any]]:
        try:
            if quarter not in (1, 2, 3, 4):
                self._logger.error(f"Некорректный номер квартала: {quarter}")
                return []

            month_start = (quarter - 1) * 3 + 1
            start_date = datetime.date(year, month_start, 1)

            # начало следующего квартала
            if quarter == 4:
                end_date = datetime.date(year + 1, 1, 1)
            else:
                end_date = datetime.date(year, month_start + 3, 1)

            query = (
                self.session.query(Report)
                .filter(Report.date >= start_date, Report.date < end_date)
                .all()
            )

            rows = []
            for record in query:
                row_dict = {}
                for col in Report.__table__.columns:
                    value = getattr(record, col.name)
                    row_dict[col.name] = value
                rows.append(row_dict)
            return rows

        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка в get_quarter_report({quarter=}, {year=}): {e}")
            self._logger.debug(traceback.format_exc())
            return []

    def get_card(self, table_name: str, card_id: str) -> Optional[Dict[str, str]]:
        """
        Получает одну запись по ID из указанной таблицы ('songs' или 'report')
        и возвращает как словарь: {field_name: value, ...}.

        :param table_name: имя таблицы ('songs' или 'report')
        :param card_id: строковое значение ID записи
        :return: словарь значений полей или None, если запись не найдена
        """
        model = self.model_map.get(table_name.lower())
        if not model:
            self._logger.error(f"Недопустимое имя таблицы в get_card: {table_name}")
            return None

        try:
            record = self.session.get(model, int(card_id))
            if not record:
                self._logger.warning(
                    f"Запись с ID {card_id} не найдена в {table_name}")
                return None

            return {col.name: getattr(record, col.name) for col in model.__table__.columns}

        except SQLAlchemyError as e:
            self._logger.error(
                f"Ошибка базы данных в get_card('{table_name}', '{card_id}'): {e}")
            self._logger.debug(traceback.format_exc())
            return None

    def add_card(self, table_name: str, payload: dict) -> Optional[str]:
        """
        Добавляет новую запись в указанную таблицу (songs или report).

        :param table_name: Название таблицы ('songs' или 'report').
        :param payload: Словарь с данными.
        """

        model_cls = self.model_map.get(table_name.lower())
        if not model_cls:
            self._logger.error(f"add_card: неизвестная таблица '{table_name}'")
            return None

        try:
            # Удаляем 'ID', 'id' и пустые строки
            payload.pop("ID", None)
            payload.pop("id", None)

            new_instance = model_cls(**payload)
            self.session.add(new_instance)
            self.session.commit()

            card_id = str(new_instance.id)
            # если нужно — можно отправить card_id через EventBus, как в flashcard-логике
            self._logger.debug(f"Карточка (ID: {card_id}) "
                               f"добавлена в таблицу '{table_name}'")
            return card_id

        except Exception as e:
            self._logger.error(f"Ошибка при добавлении записи в таблицу '{table_name}': {e}")
            self._logger.debug(traceback.format_exc())
            self.session.rollback()
            return None

    def update_card(self, card_id: str, table_name: str, payload: dict) -> None:
        """
        Обновляет запись в указанной таблице по ID.

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

            for key, value in payload.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            self.session.commit()
            self._logger.debug(f"Карточка с (ID: {card_id}) обновлена в таблице '{table_name}'")

        except Exception as e:
            self._logger.error(f"Ошибка при обновлении записи ID={card_id} в таблице '{table_name}': {e}")
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
                f"Удалено {count} карточек из таблицы '{table_name}' с IDs: {deleted_ids}")

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

    def get_settings(self) -> Dict[str, Any]:
        """
        Возвращает все настройки из таблицы `settings` как словарь.
        """
        try:
            rows = self.session.query(Settings).all()
            return {
                row.key: json.loads(row.value)
                for row in rows
            }
        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка при чтении настроек: {e}")
            self._logger.debug(traceback.format_exc())
            return {}

    def set_settings(self, settings: Dict[str, Any]) -> None:
        """
        Устанавливает или обновляет таблицу настроек.

        :param settings: словарь ключей и значений
        """
        try:
            for key, value in settings.items():
                value_json = json.dumps(value)
                existing = self.session.get(Settings, key)
                if existing:
                    existing.value = value_json
                else:
                    self.session.add(Settings(key=key, value=value_json))
            self.session.commit()
        except SQLAlchemyError as e:
            self._logger.error(f"Ошибка при записи настроек: {e}")
            self._logger.debug(traceback.format_exc())
            self.session.rollback()

    def close(self):
        """
        Закрывает соединение.
        """
        self.session.close()