import logging
from queue import Queue
from typing import Tuple


class ClassNameFilter(logging.Filter):
    """
    A logging filter that extracts the final part of the module name
    (excluding the package path) and adds it as the `class_name` attribute.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Modify the log record by adding the `class_name` attribute.

        :param record: The log record being processed.
        :return: Always returns True to allow the record to be logged.
        """
        record.class_name = record.name.split('.')[-1]
        return True


class TkinterTextHandler(logging.Handler):
    """
    A custom logging handler that redirects log messages to a queue.
    This allows safe inter-thread communication between logging
    and the Tkinter main thread.
    """

    def __init__(self, queue: Queue[Tuple[str, str]]) -> None:
        """
        Initialize the log handler.

        :param queue: A thread-safe queue for storing log messages.
        """
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process and output a log message to the queue.

        :param record: The log record to be displayed.
        """
        msg = self.format(record)
        self.queue.put((msg, record.levelname.lower()))


def set_logging_config(queue: Queue[Tuple[str, str]]) -> None:
    """
    Configure logging to output to a Tkinter-compatible queue.

    :param queue: A thread-safe queue for collecting log messages.
    :return: The configured log handler.
    """
    log_handler = TkinterTextHandler(queue)

    formatter = logging.Formatter(
        "%(asctime)s - %(class_name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_handler.setFormatter(formatter)
    log_handler.addFilter(ClassNameFilter())

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.DEBUG)
