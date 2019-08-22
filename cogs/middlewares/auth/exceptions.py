"""
Copyright (c) 2017, 2018 Genome Research Ltd.

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

from abc import ABCMeta, abstractmethod
from typing import TypeVar

from aiohttp.web import Response

from cogs.common.exceptions import CoGSError


class AuthenticationError(CoGSError):
    """ Generic authentication error """


class UnknownUserError(AuthenticationError):
    """ Raised on unknown user """


class NotLoggedInError(AuthenticationError):
    """ Raised when you're not attempting to be logged in at all """


_ResponseT = TypeVar("_ResponseT", bound=Response)


class SessionTimeoutError(AuthenticationError, metaclass=ABCMeta):
    """ Raised if a session has expired """
    @abstractmethod
    def clear_session(self, response: _ResponseT) -> _ResponseT:
        """ Clear the session """
