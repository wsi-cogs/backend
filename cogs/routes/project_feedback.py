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

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template
from cogs.security.middleware import permit

from cogs.db.models import ProjectGrade
from cogs.mail import sanitise


@template('project_feedback.jinja2')
@permit("view_projects_predeadline")
async def project_feedback(request: Request) -> Dict:
    db = request.app["db"]
    project_id = int(request.match_info["project_id"])
    user = request["user"]
    navbar_data = request["navbar"]
    project = db.get_project_id(project_id)
    if user not in (project.supervisor, project.cogs_marker):
        return web.Response(status=403, text="You aren't assigned to mark this project")
    if project.grace_passed is not True:
        return web.Response(status=403, text="This project hasn't been uploaded yet")
    if user == project.supervisor and project.supervisor_feedback:
        return web.Response(status=403, text="You have already marked this project")
    if user == project.cogs_marker and project.cogs_feedback:
        return web.Response(status=403, text="You have already marked this project")
    return {"project": project,
            "grades": request.app["config"]["misc"]["grades"],
            "label": "Submit feedback",
            **navbar_data}


@permit("view_projects_predeadline")
async def on_submit(request: Request) -> Response:
    session = request.app["session"]
    user = request["user"]
    db = request.app["db"]
    mail = request.app["mailer"]
    project_id = int(request.match_info["project_id"])
    project = db.get_project_id(session, project_id)
    if user not in (project.supervisor, project.cogs_marker):
        return web.Response(status=403, text="You aren't assigned to mark this project")
    if project.grace_passed is not True:
        return web.Response(status=403, text="This project hasn't been uploaded yet")
    if user == project.supervisor and project.supervisor_feedback:
        return web.Response(status=403, text="You have already marked this project")
    if user == project.cogs_marker and project.cogs_feedback:
        return web.Response(status=403, text="You have already marked this project")
    post = await request.post()
    grade = ProjectGrade(grade_id=int(post["options"])-1,
                         good_feedback=sanitise(post["good"]),
                         bad_feedback=sanitise(post["bad"]),
                         general_feedback=sanitise(post["general"]))
    session.add(grade)
    session.flush()
    if user == project.supervisor:
        project.supervisor_feedback_id = grade.id
    elif user == project.cogs_marker:
        project.cogs_feedback_id = grade.id
    else:
        # Should never happen because we're already checked they are
        return web.Response(status=500, text="Not logged in as right user")
    session.commit()
    await mail.send(project.student,
                    "feedback_given",
                    project=project,
                    grade=grade,
                    marker=user)
    for user in db.get_users_by_permission("create_project_groups"):
        await mail.send(user,
                        "feedback_given",
                        project=project,
                        grade=grade,
                        marker=user)

    return web.Response(status=200, text="/")
