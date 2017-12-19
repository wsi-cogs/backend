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

from cogs.common.constants import PROGRAMMES
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template
from cogs.mail import sanitise


@template('project_edit.jinja2')
async def project_edit(request: Request) -> Dict:
    """
    Edit a project.
    This view should only be allowed if the project group is not read only and the logged
    in user is the owner of the project.

    :param request:
    :return:
    """
    db = request.app["db"]
    project_name = request.match_info["project_name"]
    project = db.get_project_by_name(project_name)
    navbar_data = request["navbar"]
    if project is None:
        return web.Response(status=404)
    if request["user"] != project.supervisor:
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    return {"project": project,
            "label": "Submit",
            "show_delete_button": True,
            "cur_option": "create_project",
            "programmes": PROGRAMMES,
            **navbar_data}


async def on_submit(request: Request) -> Response:
    """
    Update a project in the database.
    Redirect the user to the new location for the project if the title is changed
    This view should only be allowed if the project group is not read only and the logged

    :param request:
    :return:
    """
    db = request.app["db"]
    project_name = request.match_info["project_name"]
    project = db.get_project_by_name(project_name)
    if request["user"] != project.supervisor:
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    post = await request.post()
    try:
        project.programmes = "|".join(post.getall("programmes"))
    except KeyError:
        project.programmes = ""
    project.title = post["title"]
    project.is_wetlab = post["options"] in ("wetlab", "both")
    project.is_computational = post["options"] in ("computational", "both")
    project.small_info = post["authors"]
    project.abstract = sanitise(post["message"])
    db.commit()
    # TODO This doesn't seem like an appropriate response...
    return web.Response(status=200, text=f"/")


async def on_delete(request: Request) -> Response:
    db = request.app["db"]
    project_name = request.match_info["project_name"]
    project = db.get_project_by_name(project_name)
    if request["user"] != project.supervisor:
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    db.session.delete(project)
    db.commit()
    # TODO This doesn't seem like an appropriate response...
    return web.Response(status=200, text=f"/")
