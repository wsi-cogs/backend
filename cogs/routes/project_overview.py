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

from aiohttp.web import Request, Response, HTTPNotFound, HTTPForbidden
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

    return {
        # FIXME Refactor this call to a quarantined function...
        # "project_list": set_group_attributes(request.app, cookies, group),
        "user":         user,
        "show_vote":    user.role.join_projects,
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

    # FIXME Refactor this call to a quarantined function
    # projects = (
    #     set_group_attributes(request.app, cookies, group)
    #     for group in groups
    #     if user.can_view_group(group))

    return {
        "series_list": projects,
        "user":        user,
        "cur_option":  "projects",
        **navbar_data}
