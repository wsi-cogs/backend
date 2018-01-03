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

from typing import Dict

from aiohttp.web import Request, Response
from aiohttp_jinja2 import template

from cogs.security.middleware import permit


@permit("create_project_groups")
@template("finalise_cogs.jinja2")
async def edit_cogs(request:Request) -> Dict:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "create_project_groups" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    group = db.get_most_recent_group()

    return {
        "projects":     [project for project in group.projects if project.student],
        "cogs_members": db.get_users_by_permission("review_other_projects"),
        "show_back":    False,
        "cur_option":   "edit_cogs",
        "use_fluid":    True,
        **navbar_data}


@permit("create_project_groups")
async def on_submit_cogs(request:Request) -> Response:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "create_project_groups" permissions

    :param request:
    :return:
    """
    db = request.app["db"]

    post = await request.post()

    for project_id, cogs_member_id in post.items():
        project = db.get_project_by_id(int(project_id))
        project.cogs_marker_id = None if cogs_member_id == "-1" else int(cogs_member_id)

    db.commit()

    # TODO This doesn't seem like an appropriate response...
    # FIXME This conflates the semantics of POST and PUT
    # It looks rather awkward to fix - the route handlers
    # would require changing to handle 2 different modes of operation
    rtn = "/finalise_choices" if request.method == "PUT" else "/"
    return Response(status=200, text=rtn)
