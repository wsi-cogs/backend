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

from aiohttp.web import Request
from aiohttp_jinja2 import template


@template("user_page.jinja2")
async def user_page(request: Request) -> Dict:
    """
    Set the template context for the user. Show the projects they:
    * Own (including legacy projects);
    * Are involved with;
    * Are in the process of signing up for, front loaded

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]


    data = {
        "user":          user,
        "cur_option":    "cogs",
        "first_option":  user.first_option,
        "second_option": user.second_option,
        "third_option":  user.third_option,
        **navbar_data}

    if user.role.create_project_groups:
        group = db.get_most_recent_group()
        data["groups"] = db.get_project_groups_by_series(group.series)

    if user.role.review_other_projects:
        data["review_list"] = series_list = db.get_projects_by_cogs_marker(user)
        for series in series_list:
            series.sort(key=lambda p: p.can_mark(user))

    if user.role.join_projects:
        data["project_list"] = db.get_projects_by_student(user)

    if user.role.create_projects:
        data["series_list"] = series_list = []
        for series in db.get_all_series():
            for group in db.get_project_groups_by_series(series):
                projects = db.get_projects_by_supervisor(user, group)
                if projects:
                    series_list.append(sorted(projects, key=lambda p: p.can_mark(user)))

    return data
