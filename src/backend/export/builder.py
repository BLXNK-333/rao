from typing import Union
import logging
from pathlib import Path

from ...entities import MonthReport, QuarterReport
from ...eventbus import EventBus, Event, Subscriber
from ...enums import EventType, DispatcherType



class ReportBuilder:
    month_table_headers = [
        "Название фонограммы",
        "Автор музыки",
        "Автор слов",
        "Кол - во сообщений в эфир",
        "Исполнитель (ФИО исполнителя или названия коллектива)",
        "Изготовитель фонограммы"
    ]

    quarter_table_headers = [
        "Наименование передачи",
        "Дата и время выхода (число, часы, мин.)",
        "Название музыкальных и иных произведений, используемых в программе",
        "ФИО композитора",
        "ФИО автора текста",
        "Длительность звучания произведения",
        "Коли-чество испол-нений",
        "Общий хронометраж",
        "Жанр произведения",
        "Исполнитель"
    ]

    RU_MONTHS_GEN = {
        1: "январь", 2: "февраль", 3: "март", 4: "апрель",
        5: "май", 6: "июнь", 7: "июль", 8: "август",
        9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"
    }

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._formats = ('xlsx', 'csv')
        self.subscribe()

    def subscribe(self):
        for event, handler in [
            (EventType.BACK.DB.REPORT, self.generate_report)
        ]:
            EventBus.subscribe(
                event_type=event,
                subscriber=Subscriber(
                    callback=handler,
                    route_by=DispatcherType.COMMON
                )
            )

    def generate_report(self, report: Union[MonthReport, QuarterReport]):
        if not self._is_valid_format(report):
            return

        if not self._is_valid_path(report):
            return

        if not self._has_data(report):
            return

        self._export(report)

    def _is_valid_format(self, report) -> bool:
        if report.file_format not in self._formats:
            self._logger.warning(
                f"Формат '{report.file_format}' не поддерживается. "
                f"Поддерживаемые форматы: {self._formats}."
            )
            return False
        return True

    def _is_valid_path(self, report) -> bool:
        path = Path(report.save_path).parent
        if not path.exists() or not path.is_dir():
            message = f"Каталог для сохранения отчёта недоступен или не существует: {path}"
            EventBus.publish(Event(event_type=EventType.BACK.EXPORT.MESSAGE), message)
            self._logger.warning(f"Пропущен экспорт: {message}")
            return False
        return True

    def _has_data(self, report) -> bool:
        if report.data:
            return True

        if isinstance(report, MonthReport):
            message = (f"За {self.RU_MONTHS_GEN[report.month]} {report.year} "
                       f"года нет данных для экспорта.")
        else:
            message = (f"За {report.quarter}-й квартал {report.year} "
                       f"года нет данных для экспорта.")

        EventBus.publish(Event(event_type=EventType.BACK.EXPORT.MESSAGE), message)

        self._logger.warning(f"Пропущен экспорт: {message}")
        return False

    def _export(self, report):
        if isinstance(report, MonthReport):
            headers = self.month_table_headers
            label = "Месячный"
            args = {"month": report.month, "year": report.year}
        elif isinstance(report, QuarterReport):
            headers = self.quarter_table_headers
            label = "Квартальный"
            args = {"quarter": report.quarter, "year": report.year}
        else:
            self._logger.warning("Неверный тип отчета.")
            return

        if report.file_format == "xlsx":
            from .xlsx import generate_xlsx_month_report, generate_xlsx_quarter_report
            func = generate_xlsx_month_report if isinstance(
                report, MonthReport) else generate_xlsx_quarter_report

            func(
                data=report.data,
                save_path=report.save_path,
                table_headers=headers,
                **args
            )
        else:
            from .csv import generate_csv_report
            generate_csv_report(
                data=report.data,
                save_path=report.save_path,
                table_headers=headers
            )

        self._logger.info(f"{label} отчет экспортирован {report.save_path}")

