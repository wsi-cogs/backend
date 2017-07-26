from aiohttp import web
from aiohttp_jinja2 import template
from permissions import view_only
from datetime import datetime
from db import ProjectGroup
from project import get_most_recent_group


@template("group_create.jinja2")
@view_only("create_project_groups")
async def group_create(request):
    return {}


@view_only("create_project_groups")
async def on_submit(request):
    session = request.app["session"]
    most_recent = get_most_recent_group(session)
    series = most_recent.series + most_recent.part // 3
    part = (most_recent.part % 3) + 1
    post = await request.post()
    group = ProjectGroup(supervisor_submit=datetime.strptime(post["supervisor_submit"], "%d/%m/%Y"),
                         grad_office_review=datetime.strptime(post["grad_office_review"], "%d/%m/%Y"),
                         student_invite=datetime.strptime(post["student_invite"], "%d/%m/%Y"),
                         student_choice=datetime.strptime(post["student_choice"], "%d/%m/%Y"),
                         student_complete=datetime.strptime(post["student_complete"], "%d/%m/%Y"),
                         initial_mark=datetime.strptime(post["initial_mark"], "%d/%m/%Y"),
                         cogs_mark=datetime.strptime(post["cogs_mark"], "%d/%m/%Y"),
                         series=series,
                         part=part,
                         read_only=False)
    session.add(group)
    most_recent.read_only = True
    session.commit()
    return web.Response(status=200, text="/dashboard")
