"""
Copyright (c) 2017, 2018 Genome Research Ltd.

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

from aiohttp.web import Request, Response, HTTPForbidden, HTTPInternalServerError
from aiohttp_jinja2 import template

from cogs.common.constants import GRADES
from cogs.db.models import ProjectGrade
from cogs.mail import sanitise
from cogs.security.middleware import permit


@template("project_feedback.jinja2")
@permit("view_projects_predeadline")
async def project_feedback(request:Request) -> Dict:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "view_projects_predeadline" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]

    project_id = int(request.match_info["project_id"])
    project = db.get_project_by_id(project_id)

    if user not in (project.supervisor, project.cogs_marker):
        raise HTTPForbidden(text="You aren't assigned to mark this project")

    if project.grace_passed is not True:
        raise HTTPForbidden(text="This project hasn't been uploaded yet")

    if user == project.supervisor and project.supervisor_feedback:
        raise HTTPForbidden(text="You have already marked this project")

    if user == project.cogs_marker and project.cogs_feedback:
        raise HTTPForbidden(text="You have already marked this project")

    return {
        "project": project,
        "grades":  GRADES,
        "label":   "Submit feedback",
        **navbar_data}


@permit("view_projects_predeadline")
async def on_submit(request:Request) -> Response:
    """
    TODO Docstring

    NOTE This handler should only be allowed if the current user has
    "view_projects_predeadline" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    mail = request.app["mailer"]

    project_id = int(request.match_info["project_id"])
    project = db.get_project_by_id(project_id)

    if user not in (project.supervisor, project.cogs_marker):
        raise HTTPForbidden(text="You aren't assigned to mark this project")

    if project.grace_passed is not True:
        raise HTTPForbidden(text="This project hasn't been uploaded yet")

    if user == project.supervisor and project.supervisor_feedback:
        raise HTTPForbidden(text="You have already marked this project")

    if user == project.cogs_marker and project.cogs_feedback:
        raise HTTPForbidden(text="You have already marked this project")

    post = await request.post()

    grade = ProjectGrade(
        grade_id         = int(post["options"]) - 1,
        good_feedback    = sanitise(post["good"]),
        bad_feedback     = sanitise(post["bad"]),
        general_feedback = sanitise(post["general"]))

    db.add(grade)
    db.session.flush()

    if user == project.supervisor:
        project.supervisor_feedback_id = grade.id

    elif user == project.cogs_marker:
        project.cogs_feedback_id = grade.id

    db.commit()

    mail.send(project.student, "feedback_given", project=project, grade=grade, marker=user)
    for user in db.get_users_by_permission("create_project_groups"):
        mail.send(user, "feedback_given", project=project, grade=grade, marker=user)

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="/")
