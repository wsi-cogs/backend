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

from aiohttp.web import Request, HTTPNotFound, HTTPForbidden
from aiohttp_jinja2 import template


@template("group_overview.jinja2")
async def group_overview(request:Request) -> Dict:
    """
    Find the correct group and send it to the user

    :param request:
    :return Response:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]

    most_recent = db.get_most_recent_group()

    if "group_series" in request.match_info:
        series = int(request.match_info["group_series"])
        part = int(request.match_info["group_part"])
        group = db.get_project_group(series, part)

    else:
        group = most_recent

    if group is None:
        raise HTTPNotFound(text="No projects found")

    elif group is most_recent and not user.can_view_group(group):
        raise HTTPForbidden(text="Cannot view rotation")

    project_list = group.projects
    project_list.sort(key=lambda p: p.supervisor.name)
    project_list.sort(key=lambda p: p.can_mark(user))

    return {"project_list": project_list,
            "user":         user,
            "show_vote":    user.role.join_projects and group.student_choosable,
            "cur_option":   "projects",
            **navbar_data}


@template("group_list_overview.jinja2")
async def series_overview(request:Request) -> Dict:
    """
    Find the correct series as well as all groups in that series

    :param request:
    :return Response:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]

    series = int(request.match_info["group_series"])
    groups = db.get_project_groups_by_series(series)

    projects = []
    for group in groups:
        if user.can_view_group(group):
            project_list = group.projects
            project_list.sort(key=lambda p: p.supervisor.name)
            project_list.sort(key=lambda p: p.can_mark(user))
            projects.append(group)

    return {"series_list": projects,
            "user":        user,
            "cur_option":  "projects",
            **navbar_data}
