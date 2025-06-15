import logging
from queue import Queue

from .db.sync_db import SyncDB
from .export.builder import ReportBuilder
from ..enums import DispatcherType, EventType
from ..eventbus import EventBus, Subscriber


class BackendService:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.msg_queue = Queue()
        self.sync_db = SyncDB()
        self.report_builder = ReportBuilder()

        self.subscribe()

    def subscribe(self):
        subscriptions = [
            (EventType.VIEW.TERM.STOP, self.stop_signal)
        ]

        for event, callback in subscriptions:
            EventBus.subscribe(event, Subscriber(
                callback=callback, route_by=DispatcherType.COMMON
            ))

    def stop_signal(self):
        self._logger.warning("Эта кнопка пока не работает")


