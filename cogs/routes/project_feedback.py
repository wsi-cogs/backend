from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from cogs.db.models import ProjectGrade
from cogs.db.functions import get_project_id, get_user_id, get_navbar_data
from mail import clean_html, send_user_email
from permissions import view_only, get_users_with_permission


@template('project_feedback.jinja2')
@view_only("view_projects_predeadline")
async def project_feedback(request: Request) -> Dict:
    session = request.app["session"]
    cookies = request.cookies
    project_id = int(request.match_info["project_id"])
    logged_in_user = get_user_id(request.app, cookies)
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
            "grades": request.app["config"]["misc"]["grades"],
            "label": "Submit feedback",
            **get_navbar_data(request)}


@view_only("view_projects_predeadline")
async def on_submit(request: Request) -> Response:
    session = request.app["session"]
    cookies = request.cookies
    logged_in_user = get_user_id(request.app, cookies)
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
                         good_feedback=clean_html(post["good"]),
                         bad_feedback=clean_html(post["bad"]),
                         general_feedback=clean_html(post["general"]))
    session.add(grade)
    session.flush()
    if logged_in_user == project.supervisor:
        project.supervisor_feedback_id = grade.id
    elif logged_in_user == project.cogs_marker:
        project.cogs_feedback_id = grade.id
    else:
        return web.Response(status=500, text="Not logged in as right user")
    grade.grade = request.app["config"]["misc"]["grades"][grade.grade_id]
    session.commit()
    await send_user_email(request.app,
                          project.student,
                          "feedback_given",
                          project=project,
                          grade=grade,
                          marker=logged_in_user)
    for user in get_users_with_permission(request.app, "create_project_groups"):
        await send_user_email(request.app,
                              user,
                              "feedback_given",
                              project=project,
                              grade=grade,
                              marker=logged_in_user)

    return web.Response(status=200, text="/")
