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
from typing import DefaultDict, Dict, List

from aiohttp.web import Request, Response
from aiohttp_jinja2 import template

from cogs.common.constants import JOB_HAZARD_FORM
from cogs.db.models import Project, User
from cogs.security.middleware import permit, permit_when_set


@permit_when_set("can_finalise")
@permit("set_readonly")
@template("finalise_cogs.jinja2")
async def finalise_cogs(request:Request) -> Dict:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "set_readonly" permissions and the latest project group has
    "can_finalise" set

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    group = db.get_most_recent_group()

    return {
        "projects":     [project for project in group.projects if project.student],
        "cogs_members": db.get_users_by_permission("review_other_projects"),
        "show_back":    True,
        "cur_option":   "finalise_choices",
        "use_fluid":    True,
        **navbar_data}


@permit_when_set("can_finalise")
@permit("set_readonly")
async def on_submit_cogs(request:Request) -> Response:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "set_readonly" permissions and the latest project group has
    "can_finalise" set

    :param request:
    :return:
    """
    db = request.app["db"]
    mail = request.app["mailer"]

    group = db.get_most_recent_group()
    group.student_uploadable = True

    supervisors:DefaultDict[User, List[Project]] = defaultdict(list)

    for project in filter(lambda p: p.student, group.projects):
        student = project.student
        project.student_uploadable = True

        try:
            choice = (student.first_option, student.second_option, student.third_option).index(project)
        except ValueError:
            choice = 3

        student.priority += (2 ** choice) - 1
        student.first_option = None
        student.second_option = None
        student.third_option = None

        mail.send(student, "project_selected_student", project=project)
        supervisors[project.supervisor].append(project)

    post = await request.post()
    for project_id, cogs_member_id in post.items():
        project = db.get_project_by_id(int(project_id))
        project.cogs_marker_id = None if cogs_member_id == "-1" else int(cogs_member_id)

    for supervisor in db.get_users_by_permission("create_projects"):
        projects = db.get_projects_by_supervisor(supervisor, group)

        if projects:
            mail.send(supervisor, "project_selected_supervisor", JOB_HAZARD_FORM, projects=projects)

    group.can_finalise = False
    group.student_choosable = False
    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="/")
