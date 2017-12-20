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

from cogs.security.middleware import permit, permit_when_set


# User model attributes for project options
_ATTRS = ("first_option_id", "second_option_id", "third_option_id")

@permit_when_set("student_choosable")
@permit("join_projects")
async def on_submit(request:Request) -> Response:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "join_projects" permissions and the latest project group has
    "student_choosable" set

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]

    post = await request.post()
    option = int(post["order"]) - 1

    project = db.get_project_by_id(int(post["choice"]))
    if not db.can_student_choose_project(user, project):
        raise HTTPForbidden(text="You cannot choose this project")

    setattr(user, _ATTRS[option], project.id)
    for i, attr in enumerate(_ATTRS):
        if i != option and getattr(user, attr) == project.id:
            setattr(user, attr, None)

    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="set")
