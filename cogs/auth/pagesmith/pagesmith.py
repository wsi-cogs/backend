"""
Copyright (c) 2017, 2018 Genome Research Ltd.

Authors:
* Christopher Harrison <ch12@sanger.ac.uk>
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

import base64
import json
import asyncio
from datetime import datetime
from typing import Dict, NamedTuple
from urllib.parse import unquote
from aiohttp.web import HTTPGatewayTimeout

import MySQLdb

from cogs.auth.abc import BaseAuthenticator
from cogs.auth.exceptions import UnknownUserError
from cogs.common import logging
from cogs.common.types import Cookies
from cogs.db.interface import Database
from cogs.db.models import User
from .crypto import BlowfishCBCDecrypt
from .exceptions import InvalidPagesmithUserCookie, NoPagesmithUserCookie


def _b64decode(data:bytes) -> bytes:
    """
    Base64 decode web-safe input

    NOTE We have to add additional base64 padding characters because of
    a bug in Pagesmith

    :param data:
    :return:
    """
    return base64.b64decode(data + b"==", b"-_")


class _AuthenticatedUser(NamedTuple):
    """ Authenticated user cache record """
    user:User
    expiry:datetime


class PagesmithAuthenticator(BaseAuthenticator, logging.LogWriter):
    """ Pagesmith authentication """
    _cogs_db:Database
    _pagesmith_db:MySQLdb.Connection
    _cache:Dict[str, _AuthenticatedUser]
    _crypto:BlowfishCBCDecrypt

    max_attempts = 3

    def __init__(self, database:Database, config:Dict) -> None:
        """
        Constructor: Set up necessary state for authentication,
        including a cache of already-authenticated users

        :param database:
        :param config:
        :return:
        """
        self._cogs_db = database

        self.log(logging.DEBUG, "Connecting to Pagesmith authentication database at {host}:{port}".format(**config["database"]))
        self._pagesmith_db = MySQLdb.connect(**config["database"])

        self._cache = {}
        self._crypto = BlowfishCBCDecrypt(config["passphrase"].encode())

    async def get_email_by_uuid(self, uuid:str) -> str:
        """
        Fetch the e-mail address by the given UUID from the Pagesmith DB

        :param uuid:
        :return:
        """
        attempt_left = PagesmithAuthenticator.max_attempts
        retry_time = 0
        while attempt_left:
            try:
                with self._pagesmith_db.cursor() as cursor:
                    _ = cursor.execute("""
                        select content
                        from   session
                        where  type = 'User'
                        and    session_key = %s
                    """, (uuid,))

                    ciphertext, = cursor.fetchone() or (None,)
                    break
            except MySQLdb.OperationError:
                self.log(logging.ERROR, f"SQL database went away, retrying in {retry_time} seconds")
                await asyncio.sleep(retry_time)
                retry_time = retry_time * 2 or retry_time + 1
                attempt_left -= 1
        if attempt_left == 0:
            self.log(logging.ERROR, f"SQL database went away, could not reconnect.")
            raise HTTPGatewayTimeout("Login service not responding")

        if not ciphertext:
            raise UnknownUserError("User not found in Pagesmith database")

        # NOTE We have to strip the first character before we decrypt
        # because it's some weird in-band Perl flag
        ciphertext = _b64decode(ciphertext[1:])
        decrypted = self._crypto.decrypt(ciphertext)
        data_json = json.loads(decrypted)

        return data_json["email"]

    async def get_user_from_source(self, cookies:Cookies) -> User:
        """
        Authenticate and fetch the user from the Pagesmith user cookie
        (or cache, if available)

        :param cookies:
        :return:
        """
        try:
            # NOTE We have to percent decode the input because of a bug
            # in Pagesmith
            pagesmith_user = unquote(cookies["Pagesmith_User"])

        except KeyError:
            raise NoPagesmithUserCookie("No Pagesmith user cookie available")

        # Get from cache, if available
        if pagesmith_user in self._cache:
            email, expiry = self._cache[pagesmith_user]
            if expiry > datetime.utcnow():
                return email

            # Invalidate expired logins
            del self._cache[pagesmith_user]

        try:
            ciphertext = _b64decode(pagesmith_user.encode())
            decrypted = self._crypto.decrypt(ciphertext)
            _perm, uuid, _refresh, expiry, _ip = decrypted.split(b" ")

            uuid = uuid.decode()
            expiry = datetime.utcfromtimestamp(float(expiry))

        except:
            raise InvalidPagesmithUserCookie("Could not parse Pagesmith user cookie")

        email = await self.get_email_by_uuid(uuid)
        user = self._cogs_db.get_user_by_email(email)

        if not user:
            raise UnknownUserError("User not found in CoGS database")

        self._cache[pagesmith_user] = _AuthenticatedUser(user, expiry)

        return user
