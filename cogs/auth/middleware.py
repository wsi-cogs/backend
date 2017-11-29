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

from aiohttp import web

from cogs.auth.exceptions import AuthenticationError
from cogs.common.types import Handler


async def authentication(app:web.Application, handler:Handler) -> Handler:
    """
    Authentication middleware factory

    NOTE The authentication handler is threaded through the application
    under the "auth" key

    :param app:
    :param handler:
    :return:
    """
    auth = app["auth"]

    async def _middleware(request:web.Request) -> web.Response:
        """
        Authentication middleware: Extract the user from the cookies and
        thread it through the request under the "user" key

        :param request:
        :return:
        """
        try:
            cookies = request.cookies
            request["user"] = auth.get_user_from_source(cookies)

        except AuthenticationError as e:
            # Raise "403 Forbidden" exception (n.b., we use 403 instead
            # of 401 because authentication is cookie-based, rather than
            # using the Authorization request header)
            # TODO This could be better...
            exc_name = e.__class__.__name__
            raise web.HTTPForbidden(reason=f"{exc_name}: {e}")

        return await handler(request)

    return _middleware