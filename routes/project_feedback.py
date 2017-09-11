from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from db import ProjectGrade
from db_helper import get_project_id, get_user_id
from mail import send_user_email
from permissions import view_only


@template('project_feedback.jinja2')
@view_only("view_projects_predeadline")
async def project_feedback(request: Request) -> Dict:
    session = request.app["session"]
    cookies = request.cookies
    project_id = int(request.match_info["project_id"])
    logged_in_user = get_user_id(session, cookies)
    project = get_project_id(session, project_id)
    if logged_in_user not in (project.supervisor, project.cogs_marker):
        return web.Response(status=403, text="You aren't assigned to mark this project")
    if project.grace_passed is not True:
        return web.Response(status=403, text="This project hasn't been uploaded yet")
    if logged_in_user == project.supervisor and project.supervisor_feedback:
        return web.Response(status=403, text="You have already marked this project")
    if logged_in_user == project.cogs_marker and project.cogs_feedback:
        return web.Response(status=403, text="You have already marked this project")
    return {"project": project,
            "grades": request.app["misc_config"]["grades"],
            "label": "Submit feedback"}


@view_only("view_projects_predeadline")
async def on_submit(request: Request) -> Response:
    session = request.app["session"]
    cookies = request.cookies
    logged_in_user = get_user_id(session, cookies)
    project_id = int(request.match_info["project_id"])
    project = get_project_id(session, project_id)
    if logged_in_user not in (project.supervisor, project.cogs_marker):
        return web.Response(status=403, text="You aren't assigned to mark this project")
    if project.grace_passed is not True:
        return web.Response(status=403, text="This project hasn't been uploaded yet")
    if logged_in_user == project.supervisor and project.supervisor_feedback:
        return web.Response(status=403, text="You have already marked this project")
    if logged_in_user == project.cogs_marker and project.cogs_feedback:
        return web.Response(status=403, text="You have already marked this project")
    post = await request.post()
    grade = ProjectGrade(grade_id=int(post["options"])-1,
                         good_feedback=post["good"],
                         bad_feedback=post["bad"],
                         general_feedback=post["general"])
    session.add(grade)
    session.flush()
    if logged_in_user == project.supervisor:
        project.supervisor_feedback_id = grade.id
    elif logged_in_user == project.cogs_marker:
        project.cogs_feedback_id = grade.id
    else:
        return web.Response(status=500, text="Not logged in as right user")
    grade.grade = request.app["misc_config"]["grades"][grade.grade_id]
    session.commit()
    await send_user_email(request.app,
                          project.student,
                          "feedback_given",
                          project=project,
                          grade=grade,
                          marker=logged_in_user)

    return web.Response(status=200, text="/")
