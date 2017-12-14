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

from typing import Dict, List

from aiohttp.web import Request
from aiohttp_jinja2 import template

from cogs.db.models import Project


@template("markable_projects.jinja2")
async def markable_projects(request:Request) -> Dict:
    """
    Get all projects the user can mark

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]

    projects:List[Project] = []

    if user.role.review_other_projects:
        projects.extend(db.get_projects_by_cogs_marker(user))

    if user.role.create_projects:
        projects.extend(db.get_projects_by_supervisor(user))

    return {
        "cur_option":   "markable_projects",
        "no_projects":  "There are no projects you can mark",
        "project_list": [p for p in projects if p.can_solicit_feedback(user)],
        **navbar_data}
