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

from collections import defaultdict
from typing import DefaultDict, Dict, Set

from aiohttp.web import Request, Response
from aiohttp_jinja2 import template

from cogs.security.middleware import permit, permit_when_set


@permit_when_set("can_finalise")
@permit("set_readonly")
@template("finalise_choices.jinja2")
async def finalise_choices(request:Request) -> Dict:
    """
    Create a table with users and their choices for projects to join

    NOTE This handler should only be allowed if the current user has
    "set_readonly" permissions and the latest project group has
    "can_finalise" set

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    students = db.get_users_by_permission("join_projects")

    # A two-dimensional dictionary of users, indexed by project ID and
    # choice rank (or "length"), respectively; using defaultdict so we
    # don't have to keep doing existence checking
    project_choice_map:DefaultDict = defaultdict(lambda: defaultdict(lambda: []))

    student_has_project:Set = set()

    for user in students:
        for i, option in enumerate((user.first_option, user.second_option, user.third_option)):
            if option:
                project_choice_map[option.id][i].append(user)
                if option.student_id == user.id:
                    student_has_project.add(user.id)

    for project_id, options in project_choice_map.items():
        for option in options.values():
            option.sort(key=lambda user: user.priority, reverse=True)

        # Maximum number of students choosing a project at any choice rank
        project_choice_map[project_id]["length"] = max(len(option) for option in options.values())

    return {
        "choices":    project_choice_map,
        "students":   students,
        "student_has_project": student_has_project,
        "cur_option": "finalise_choices",
        **navbar_data}


@permit_when_set("can_finalise")
@permit("set_readonly")
async def on_submit_group(request:Request) -> Response:
    """
    Give projects tentative students, though not finalised yet

    NOTE This handler should only be allowed if the current user has
    "set_readonly" permissions and the latest project group has
    "can_finalise" set

    :param request:
    :return:
    """
    db = request.app["db"]
    group = db.get_most_recent_group()

    post = await request.post()

    for project in group.projects:
        project_id = str(project.id)
        project.student_id = int(post[project_id]) if project_id in post else None
    db.commit()

    not_all_saved = any(user for user in db.get_users_by_permission("join_projects")
                        if str(user.id) not in post.values())
    if not_all_saved:
        return Response(status=200, text="/finalise_dummy")

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="/finalise_cogs")