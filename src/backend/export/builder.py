import logging
from typing import Union

from .month.xlsx import generate_xlsx_month_report
from ...entities import MonthReport, QuarterReport
from ...eventbus import EventBus, Event, Subscriber
from ...enums import EventType, DispatcherType



class ReportBuilder:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
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
        if isinstance(report, MonthReport):
            if report.file_format == "xlsx":
                generate_xlsx_month_report(
                    month=report.month,
                    year=report.year,
                    data=report.data,
                    save_path=report.save_path
                )
        elif isinstance(report, QuarterReport):
            pass
        else:
            pass
