from aiohttp import web
from aiohttp_jinja2 import template

from db import Project
from db_helper import get_most_recent_group
from permissions import view_only


@template('project_edit.jinja2')
@view_only("create_projects")
async def project_create(request):
    """
    Create a project.
    This view should only be allowed if the current user has 'create_projects'

    :param request:
    :return:
    """
    return {"project": {}, "label": "Create"}


@view_only("create_projects")
async def on_submit(request):
    """
    Create a new project and add it to the database.
    Redirect the user to the project page of the new project once it's created
    This view should only be allowed if the current user has 'create_projects'

    :param request:
    :return:
    """
    session = request.app["session"]
    post = await request.post()
    project = Project(title=post["title"],
                      small_info=post["authors"],
                      is_wetlab="wetlab" in post,
                      is_computational="computational" in post,
                      abstract=post["message"],
                      group_id=get_most_recent_group(session).id,
                      supervisor_id=int(request.cookies["user_id"]))
    session.add(project)
    session.commit()
    return web.Response(status=200, text=f"/projects/{post['title']}/edit")
