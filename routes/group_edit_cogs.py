from aiohttp import web
from aiohttp_jinja2 import template

from db_helper import get_most_recent_group, get_project_id
from permissions import get_users_with_permission


@template('finalise_cogs.jinja2')
async def edit_cogs(request):
    session = request.app["session"]
    group = get_most_recent_group(session)
    cogs_members = list(get_users_with_permission(request.app, "review_other_projects"))
    return {"projects": [project for project in group.projects if project.student],
            "cogs_members": cogs_members,
            "show_back": False}


async def on_submit_cogs(request):
    session = request.app["session"]
    for project_id, cogs_member_id in (await request.post()).items():
        project = get_project_id(session, int(project_id))
        project.cogs_marker_id = int(cogs_member_id)
    session.commit()
    return web.Response(status=200, text="/")
