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

from aiohttp.web import Application, Request, Response, HTTPForbidden, HTTPFound

from cogs.common.types import Handler
from .abc import BaseAuthenticator
from .exceptions import AuthenticationError, NotLoggedInError, SessionTimeoutError


async def authentication(app:Application, handler:Handler) -> Handler:
    """
    Authentication middleware factory

    NOTE The authentication handler is threaded through the application
    under the "auth" key

    :param app:
    :param handler:
    :return:
    """
    auth:BaseAuthenticator = app["auth"]

    async def _middleware(request:Request) -> Response:
        """
        Authentication middleware: Extract the user from the cookies and
        thread it through the request under the "user" key

        :param request:
        :return:
        """
        try:
            cookies = request.cookies
            request["user"] = user = await auth.get_user_from_source(cookies)

        except (NotLoggedInError, SessionTimeoutError):
            raise HTTPFound("/login")

        except AuthenticationError as e:
            # Raise "403 Forbidden" exception (n.b., we use 403 instead
            # of 401 because authentication is cookie-based, rather than
            # using the Authorization request header)
            # TODO This could be better...
            exc_name = e.__class__.__name__
            raise HTTPForbidden(text=f"Permission denied\n{exc_name}: {e}")

        if not user.role:
            raise HTTPForbidden(text="No roles assigned to user.")

        return await handler(request)

    return _middleware
