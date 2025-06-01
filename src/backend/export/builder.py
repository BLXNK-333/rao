import logging
from typing import Union

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

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._formats = ('xlsx', 'xls', 'csv')
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

        if report.file_format not in self._formats:
            self._logger.warning(f"Формат '{report.file_format}' не поддерживается. "
                                 f"Поддерживаемые форматы: {self._formats}.")
            return

        if not report.data:
            message = (
                f"Нет данных за указанный период: "
                f"{report.month}/{report.year}" if isinstance(report, MonthReport)
                else f"Квартал {report.quarter} {report.year}"
            )

            EventBus.publish(
                Event(event_type=EventType.BACK.EXPORT.NO_DATA),
                message
            )

            self._logger.warning(f"Пропущен экспорт: {message}")
            return

        if isinstance(report, MonthReport):

            if report.file_format == "xlsx":
                from .xlsx import generate_xlsx_month_report
                generate_xlsx_month_report(
                    month=report.month,
                    year=report.year,
                    data=report.data,
                    save_path=report.save_path,
                    table_headers=self.month_table_headers
                )

            elif report.file_format == "xls":
                self._logger.warning("Поддержка 'xls' пока не доступна.")
                return

            else:
                from .csv import generate_csv_report
                generate_csv_report(
                    data=report.data,
                    save_path=report.save_path,
                    table_headers=self.month_table_headers
                )
            self._logger.info(f"Месячный отчет экспортирован {report.save_path}")

        elif isinstance(report, QuarterReport):

            if report.file_format == "xlsx":
                from .xlsx import generate_xlsx_quarter_report
                generate_xlsx_quarter_report(
                    quarter=report.quarter,
                    year=report.year,
                    data=report.data,
                    save_path=report.save_path,
                    table_headers=self.quarter_table_headers
                )

            elif report.file_format == "xls":
                self._logger.warning("Поддержка 'xls' пока не доступна.")
                return

            else:
                from .csv import generate_csv_report
                generate_csv_report(
                    data=report.data,
                    save_path=report.save_path,
                    table_headers=self.quarter_table_headers
                )
            self._logger.info(f"Квартальный отчет экспортирован {report.save_path}")

        else:
            self._logger.error("Неверный тип отчета.")
