"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import atexit
import logging
import sys
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from traceback import print_tb
from types import TracebackType
from typing import Callable, ClassVar, Type


# We just need one logger
_LOGGER_NAME = "cogs"


class LogWriter(object):
    """ Base class for access to logging """
    _logger:ClassVar[logging.Logger] = logging.getLogger(_LOGGER_NAME)

    def log(self, level:int, message:str) -> None:
        """
        Log message at the specified level

        :param level:
        :param message:
        :return:
        """
        self._logger.log(level, message)


def _exception_handler(logger:logging.Logger) -> Callable:
    """
    Create an exception handler that logs uncaught exceptions (except
    keyboard interrupts) and spews the traceback to stderr (in debugging
    mode) before terminating
    """
    def _log_uncaught_exception(exc_type:Type[BaseException], exc_val:BaseException, traceback:TracebackType) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_val, traceback)

        else:
            logger.critical(str(exc_val) or exc_type.__name__)
            if __debug__:
                print_tb(traceback)

            sys.exit(1)

    return _log_uncaught_exception


def initialise(level:int = DEBUG) -> logging.Logger:
    """
    Initialise and configure the logger

    NOTE This must be called before any subtypes of LogWriter are instantiated

    :param level:
    :return:
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s\t%(levelname)s\t%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ%z"
    )

    handler = logging.StreamHandler()
    atexit.register(handler.close)

    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.addHandler(handler)

    sys.excepthook = _exception_handler(logger)

    return logger
