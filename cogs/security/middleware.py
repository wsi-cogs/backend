"""
Copyright (c) 2017 Genome Research Ltd.

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

from functools import wraps

from aiohttp.web import HTTPForbidden, Request, Response

from cogs.common.types import Handler
from .roles import zero


def permit(*permissions:str) -> Handler:
    """
    Factory that returns a decorator that forbids access to route
    handlers if the authenticated user doesn't have any of the specified
    permissions

    NOTE While it works in a similar way, this should be used as a
    decorator, rather than web application middleware

    :param permissions:
    :return:
    """
    assert permissions

    def decorator(fn:Handler) -> Handler:
        @wraps(fn)
        async def decorated(request:Request) -> Response:
            """
            Check authenticated user has the necessary permissions

            :param request:
            :return:
            """
            user = request.get("user")
            role = user.role if user else zero

            if not all(getattr(role, p) for p in permissions):
                raise HTTPForbidden(text="Permission denied")

            return await fn(request)

        return decorated

    return decorator
