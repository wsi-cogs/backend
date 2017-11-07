from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from cogs.db.functions import get_most_recent_group, get_project_id, get_navbar_data
from permissions import get_users_with_permission, view_only


@view_only("create_project_groups")
@template('finalise_cogs.jinja2')
async def edit_cogs(request: Request) -> Dict:
    session = request.app["session"]
    group = get_most_recent_group(session)
    cogs_members = list(get_users_with_permission(request.app, "review_other_projects"))
    return {"projects": [project for project in group.projects if project.student],
            "cogs_members": cogs_members,
            "show_back": False,
            "cur_option": "edit_cogs",
            "use_fluid": True,
            **get_navbar_data(request)}


@view_only("create_project_groups")
async def on_submit_cogs(request: Request) -> Response:
    session = request.app["session"]
    for project_id, cogs_member_id in (await request.post()).items():
        project = get_project_id(session, int(project_id))
        if cogs_member_id == "-1":
            project.cogs_marker_id = None
        else:
            project.cogs_marker_id = int(cogs_member_id)
    session.commit()
    if request.method == "PUT":
        rtn = "/finalise_choices"
    else:
        rtn = "/"
    return web.Response(status=200, text=rtn)
