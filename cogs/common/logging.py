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
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL


# We just need one logger
_LOGGER_NAME = "cogs"


class LogWriter(object):
    """ Base class for access to logging """
    _logger:logging.Logger

    def __init__(self) -> None:
        """ Constructor: Get a reference to the logger """
        self._logger = logging.getLogger(_LOGGER_NAME)

    def log(self, level:int, message:str) -> None:
        """
        Log message at the specified level

        :param level:
        :param message:
        :return:
        """
        self._logger.log(level, message)


def initialise(level:int = DEBUG) -> logging.Logger:
    """
    Initialise and configure the logger

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

    return logger
