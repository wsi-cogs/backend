"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>

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

from cogs.db.interface import Database
from cogs.db.models import User
from .abc import BaseAuthenticator
from aiohttp.web import Request


class PagesmithDummyAuthenticator(BaseAuthenticator):
    """ Dummy pagesmith-like authenticator for debugging """
    authenticator_template = "dummy_pagesmith_login.jinja2"
    _cogs_db:Database

    def __init__(self, database:Database) -> None:
        """
        Constructor: Inject the database dependency
        """
        self._cogs_db = database

    async def get_user_from_request(self, request: Request) -> User:
        user = None
        if "email_address" in request.cookies:
            user = self._cogs_db.get_user_by_email(request.cookies["email_address"])
        if user is None:
            user = self._cogs_db.get_user_by_id(1)
        return user
