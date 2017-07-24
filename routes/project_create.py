from aiohttp_jinja2 import template
from aiohttp import web
from permissions import view_only
from db import Project
from project import get_most_recent_group


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
    session = request.app["session"]
    post = await request.post()
    post["title"] = post["title"] or "Title"
    project = Project(title=post["title"],
                      is_wetlab="wetlab" in post,
                      is_computational="computational" in post,
                      abstract=post["message"],
                      group=get_most_recent_group(session).id,
                      supervisor=int(request.cookies["user_id"]))
    session.add(project)
    session.commit()
    return web.Response(status=200, text=f"/projects/{post['title']}/edit")
