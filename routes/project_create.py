from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from db import Project
from db_helper import get_most_recent_group
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
    programmes = request.app["misc_config"]["programmes"]
    return {"project": {"programmes": ""},
            "label": "Create",
            "programmes": programmes}


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
    try:
        programmes = "|".join(post.getall("programmes"))
    except KeyError:
        programmes = ""
    project = Project(title=post["title"],
                      small_info=post["authors"],
                      is_wetlab=post["options"] in ("wetlab", "both"),
                      is_computational=post["options"] in ("computational", "both"),
                      abstract=post["message"],
                      programmes=programmes,
                      group_id=get_most_recent_group(session).id,
                      supervisor_id=int(request.cookies["user_id"]))
    session.add(project)
    session.commit()
    return web.Response(status=200, text=f"/projects/{post['title']}/edit")
