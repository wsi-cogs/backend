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

from abc import ABCMeta, abstractmethod
from aiohttp.web import Request

from cogs.db.models import User


class BaseAuthenticator(metaclass=ABCMeta):
    """ Abstact base class for authenticators """
    authenticator_template:str = ""

    @abstractmethod
    async def get_user_from_request(self, source:Request) -> User:
        """
        Authenticate and return user from some source input (e.g., HTTP
        request headers, a cookie, etc.)
        """
