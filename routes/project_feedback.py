from aiohttp import web
from aiohttp_jinja2 import template

from db import ProjectGrade
from db_helper import get_project_id
from permissions import view_only


@template('project_feedback.jinja2')
@view_only("view_projects_predeadline")
async def project_feedback(request):
    session = request.app["session"]
    project_id = request.match_info["project_id"]
    project = get_project_id(session, project_id)
    return {"project": project,
            "grades": request.app["misc_config"]["grades"],
            "label": "Submit feedback"}


@view_only("view_projects_predeadline")
async def on_submit(request):
    session = request.app["session"]
    post = await request.post()
    grade = ProjectGrade(grade=int(post["options"]),
                         good_feedback=post["good"],
                         bad_feedback=post["bad"],
                         general_feedback=post["general"])
    session.add(grade)
    session.commit()
    return web.Response(status=200, text="/dashboard")
