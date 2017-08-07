from aiohttp_jinja2 import template
from aiohttp import web
from permissions import is_user
from project import get_project_name


@template('project_edit.jinja2')
async def project_edit(request):
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
    if not is_user(request.cookies, project.supervisor):
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    return {"project": project, "label": "Update"}


async def on_submit(request):
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
    if not is_user(request.cookies, project.supervisor):
        return web.Response(status=403)
    if project.group.read_only:
        return web.Response(status=403)
    post = await request.post()
    project.title = post["title"]
    project.is_wetlab = "wetlab" in post
    project.is_computational = "computational" in post
    project.abstract = post["message"]
    session.commit()
    return web.Response(status=200, text=f"../{project.title}/edit")
