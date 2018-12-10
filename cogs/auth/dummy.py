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

from cogs.db.interface import Database
from cogs.db.models import User
from .abc import BaseAuthenticator


class DummyAuthenticator(BaseAuthenticator):
    """ Dummy authenticator for debugging """
    _db:Database
    authenticator_template = "dummy_login.jinja2"

    def __init__(self, database:Database) -> None:
        """
        Constructor: Inject the database dependency

        :param database:
        :return:
        """
        self._db = database

    async def get_user_from_request(self, _source) -> User:
        # Always return the root user if there's no authentication
        return self._db.get_user_by_id(1)
