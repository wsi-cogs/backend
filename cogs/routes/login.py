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

from aiohttp.web import Request, Response


async def login(request:Request) -> Response:
    """
    Log a user into the system and set their permissions

    FIXME I believe this is just a testing/debugging handler; it can
    probably be removed...

    :param request:
    :return:
    """
    post_req = await request.post()
    user_type = post_req["type"]

    user = request["user"]
    user.user_type = user_type
    request.app["db"].commit()  # FIXME? Is this necessary?

    return Response(text=user_type)
