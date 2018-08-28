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

from cogs.db.models import Project
from cogs.security.middleware import permit, permit_when_set


@permit_when_set("can_finalise")
@permit("set_readonly")
@template("finalise_dummy.jinja2")
async def finalise_dummy(request:Request) -> Dict:
    """
    Show the template for finalising dummy projects, though only if it's finalisable
    This is because it leads to the ultimate finalisation of projects in a non-reversible way

    NOTE This handler should only be allowed if the current user has
    "set_readonly" permissions and the latest project group has
    "can_finalise" set

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    group = db.get_most_recent_group()
    students_with_projects = [project.student_id for project in group.projects if project.student_id is not None]
    students_without_projects = [user for user in db.get_users_by_permission("join_projects")
                                 if user.id not in students_with_projects]

    return {
        "students":     students_without_projects,
        "supervisors":  db.get_users_by_permission("create_projects"),
        "cur_option":   "finalise_choices",
        **navbar_data}


@permit_when_set("can_finalise")
@permit("set_readonly")
async def on_submit_dummy(request:Request) -> Response:
    """
    Create dummy projects for the supervisors and attach students to them

    NOTE This handler should only be allowed if the current user has
    "set_readonly" permissions and the latest project group has
    "can_finalise" set

    :param request:
    :return:
    """
    db = request.app["db"]
    group = db.get_most_recent_group()

    student_supervisor_map = await request.post()
    for student_id, supervisor_id in student_supervisor_map.items():
        student_id, supervisor_id = int(student_id), int(supervisor_id)
        student = db.get_user_by_id(student_id)
        project = Project(
            title=f"Dummy project for {student.name}",
            small_info="",
            is_wetlab=False,
            is_computational=False,
            abstract="A dummy project created automatically. Please fill in the details for it once established.",
            programmes="",
            group_id=group.id,
            supervisor_id=supervisor_id,
            student_id=student_id
        )
        db.add(project)
        student.first_option = project
        db.commit()
        db.session.flush()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="/finalise_cogs")
