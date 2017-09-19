from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from db import Project
from db_helper import get_most_recent_group, get_navbar_data, get_user_cookies
from mail import clean_html
from permissions import view_only


@template('project_edit.jinja2')
@view_only("create_projects")
async def project_create(request: Request) -> Dict:
    """
    Create a project.
    This view should only be allowed if the current user has 'create_projects'

    :param request:
    :return:
    """
    session = request.app["session"]
    most_recent = get_most_recent_group(session)
    if most_recent.read_only:
        return web.Response(status=403, text="Not allowed to create groups now")
    programmes = request.app["misc_config"]["programmes"]
    return {"project": {"programmes": ""},
            "label": "Create",
            "programmes": programmes,
            **get_navbar_data(request)}


@view_only("create_projects")
async def on_submit(request: Request) -> Response:
    """
    Create a new project and add it to the database.
    Redirect the user to the project page of the new project once it's created
    This view should only be allowed if the current user has 'create_projects'

    :param request:
    :return:
    """
    session = request.app["session"]
    post = await request.post()
    most_recent = get_most_recent_group(session)
    if most_recent.read_only:
        return web.Response(status=403, text="Not allowed to create groups now")
    try:
        programmes = "|".join(post.getall("programmes"))
    except KeyError:
        programmes = ""
    project = Project(title=post["title"],
                      small_info=post["authors"],
                      is_wetlab=post["options"] in ("wetlab", "both"),
                      is_computational=post["options"] in ("computational", "both"),
                      abstract=clean_html(post["message"]),
                      programmes=programmes,
                      group_id=most_recent.id,
                      supervisor_id=get_user_cookies(request.app, request.cookies))
    session.add(project)
    session.commit()
    return web.Response(status=200, text=f"/projects/{post['title']}/edit")
