"""
This file contains the logging system for the sensor app.
It is used to log messages and errors to the user interface of the app
inside the tkinter Text widget.
"""

import logging


def setup_logging(log_message_func, debug=False):
    """
    Set up logging with a custom handler for the given log_message function
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create and add the custom handler
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    # Add the log_message function as a handler
    class FunctionHandler(logging.Handler):
        def __init__(self, log_message_func):
            super().__init__()
            self.log_message_func = log_message_func

        def emit(self, record):
            log_entry = self.format(record)
            self.log_message_func(log_entry, level=record.levelname.lower())

    function_handler = FunctionHandler(log_message_func)
    function_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    function_handler.setFormatter(formatter)
    root_logger.addHandler(function_handler)


def log_message(*, level="info", message="test"):
    """
    Log a message with the given level
    """
    logger = logging.getLogger()
    match level:
        case "debug":
            logger.debug(message)
        case "info":
            logger.info(message)
        case "warning":
            logger.warning(message)
        case "error":
            logger.error(message)
        case _:
            logger.info(message)
