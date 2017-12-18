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

from aiohttp.web import Request, Response, HTTPForbidden
from aiohttp_jinja2 import template

from cogs.common.constants import PROGRAMMES
from cogs.db.models import Project
from cogs.mail import sanitise
from cogs.security.middleware import permit


@permit("create_projects")
@template("project_edit.jinja2")
async def project_create(request:Request) -> Dict:
    """
    Create a project

    NOTE This handler should only be allowed if the current user has
    "create_projects" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    group = db.get_most_recent_group()

    if group.read_only:
        raise HTTPForbidden(text="Not allowed to create groups now")

    return {
        "project":    {"programmes": ""},
        "label":      "Submit",
        "programmes": PROGRAMMES,
        "cur_option": "create_project",
        **navbar_data}


@permit("create_projects")
async def on_submit(request:Request) -> Response:
    """
    Create a new project and add it to the database.

    TODO Redirect the user to the project page of the new project once
    it's created

    NOTE This handler should only be allowed if the current user has
    "create_projects" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    group = db.get_most_recent_group()

    post = await request.post()

    if group.read_only:
        raise HTTPForbidden(text="Not allowed to create groups now")

    try:
        programmes = "|".join(post.getall("programmes"))
    except KeyError:
        programmes = ""

    project = Project(
        title            = post["title"],
        small_info       = post["authors"],
        is_wetlab        = post["options"] in ("wetlab", "both"),
        is_computational = post["options"] in ("computational", "both"),
        abstract         = sanitise(post["message"]),
        programmes       = programmes,
        group_id         = group.id,
        supervisor_id    = user)

    db.add(project)
    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text=f"/")
