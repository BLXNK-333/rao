import logging
from queue import Queue

from .db.sync_db import SyncDB


class BackendService:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.msg_queue = Queue()
        self.sync_db = SyncDB()


