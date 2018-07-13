"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
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

from aiohttp.web import Request, Response, HTTPForbidden
from cogs.auth.dummy import DummyAuthenticator


async def login(request:Request) -> Response:
    """
    Log a user into the system and set their permissions

    This is a debugging handler used for testing permissions.
    It should never be accessible in production as it allows users to
    change their permissions without any checks

    :param request:
    :return:
    """
    if not isinstance(request.app["auth"], DummyAuthenticator):
        return HTTPForbidden("Internal login not allowed if not using DummyAuthenticator")

    post_req = await request.post()
    user_type = post_req["type"]

    user = request["user"]
    user.user_type = user_type
    request.app["db"].commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(text=user_type)
