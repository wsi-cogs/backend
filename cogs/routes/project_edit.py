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

from aiohttp.web import Request, Response, HTTPForbidden, HTTPNotFound
from aiohttp_jinja2 import template

from cogs.common.constants import PROGRAMMES
from cogs.mail import sanitise


@template("project_edit.jinja2")
async def project_edit(request:Request) -> Dict:
    """
    Edit a project

    NOTE This handler should only be allowed if the project group is not
    read only and the logged in user is the owner of the project

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]

    project_name = request.match_info["project_name"]
    project = db.get_project_by_name(project_name)

    if project is None:
        raise HTTPNotFound()

    if user != project.supervisor or project.group.read_only:
        raise HTTPForbidden()

    return {
        "project":            project,
        "label":              "Submit",
        "show_delete_button": True,
        "cur_option":         "create_project",
        "programmes":         PROGRAMMES,
        **navbar_data}


async def on_submit(request:Request) -> Response:
    """
    Update a project in the database and redirect the user to the new
    location for the project if the title is changed

    NOTE This handler should only be allowed if the project group is not
    read only and the logged in user is the owner of the project

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]

    project_name = request.match_info["project_name"]
    project = db.get_project_by_name(project_name)

    if user != project.supervisor or project.group.read_only:
        raise HTTPForbidden()

    post = await request.post()

    try:
        project.programmes = "|".join(post.getall("programmes"))
    except KeyError:
        project.programmes = ""

    project.title            = post["title"]
    project.is_wetlab        = post["options"] in ("wetlab", "both")
    project.is_computational = post["options"] in ("computational", "both")
    project.small_info       = post["authors"]
    project.abstract         = sanitise(post["message"])
    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text=f"/")


async def on_delete(request:Request) -> Response:
    """
    TODO Docstring

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]

    project_name = request.match_info["project_name"]
    project = db.get_project_by_name(project_name)

    if user != project.supervisor or project.group.read_only:
        raise HTTPForbidden()

    db.session.delete(project)
    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text=f"/")
