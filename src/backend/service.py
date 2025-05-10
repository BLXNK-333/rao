import logging
from queue import Queue


class BackendService:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.msg_queue = Queue()


