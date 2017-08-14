from aiohttp import web
from aiohttp_jinja2 import template

from db_helper import get_most_recent_group, get_project_id
from permissions import get_users_with_permission


@template('finalise_cogs.jinja2')
async def finalise_cogs(request):
    session = request.app["session"]
    group = get_most_recent_group(session)
    cogs_members = get_users_with_permission(request, "review_other_projects")
    return {"projects": [project for project in group.projects if project.student],
            "cogs_members": cogs_members}


async def on_submit_cogs(request):
    session = request.app["session"]
    for project_id, cogs_member_id in (await request.post()).items():
        project = get_project_id(session, int(project_id))
        project.cogs_marker_id = int(cogs_member_id)
    return web.Response(status=200, text="/dashboard")
