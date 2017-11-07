from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from cogs.db.functions import get_project_name, get_navbar_data
from mail import clean_html
from permissions import is_user


@template('project_edit.jinja2')
async def project_edit(request: Request) -> Dict:
    """
    Edit a project.
    This view should only be allowed if the project group is not read only and the logged
    in user is the owner of the project.

    :param request:
    :return:
    """
    session = request.app["session"]
    project_name = request.match_info["project_name"]
    project = get_project_name(session, project_name)
    if project is None:
        return web.Response(status=404)
    if not is_user(request.app, request.cookies, project.supervisor):
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    programmes = request.app["config"]["misc"]["programmes"]
    return {"project": project,
            "label": "Submit",
            "show_delete_button": True,
            "cur_option": "create_project",
            "programmes": programmes,
            **get_navbar_data(request)}


async def on_submit(request: Request) -> Response:
    """
    Update a project in the database.
    Redirect the user to the new location for the project if the title is changed
    This view should only be allowed if the project group is not read only and the logged

    :param request:
    :return:
    """
    session = request.app["session"]
    project_name = request.match_info["project_name"]
    project = get_project_name(session, project_name)
    if not is_user(request.app, request.cookies, project.supervisor):
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    post = await request.post()
    try:
        project.programmes = "|".join(post.getall("programmes"))
    except KeyError:
        project.programmes = ""
    project.title = post["title"]
    project.is_wetlab = post["options"] in ("wetlab", "both")
    project.is_computational = post["options"] in ("computational", "both")
    project.small_info = post["authors"]
    project.abstract = clean_html(post["message"])
    session.commit()
    return web.Response(status=200, text=f"/")


async def on_delete(request: Request) -> Response:
    session = request.app["session"]
    project_name = request.match_info["project_name"]
    project = get_project_name(session, project_name)
    if not is_user(request.app, request.cookies, project.supervisor):
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    session.delete(project)
    session.commit()
    return web.Response(status=200, text=f"/")
