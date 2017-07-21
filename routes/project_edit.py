from aiohttp import web
from permissions import is_user_id
from db import Project, ProjectGroup


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
    project = session.query(Project).filter_by(title=project_name).first()
    group = session.query(ProjectGroup).filter_by(id=project.group).first()
    if not is_user_id(request.cookies, project.supervisor):
        return web.Response(status=403)
    if group.read_only:
        return web.Response(status=403)
    return web.Response(text=f"{project}")

