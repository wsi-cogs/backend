from aiohttp import web
from project import get_project_name


async def project(request):
    """
    Find and render an individual project.
    This view should be able to be edited by the Supervisor who owns it.
    However, if the status of the project group is read-only, no user will be able
    to edit the project.

    :param request:
    :return:
    """
    session = request.app["session"]
    project_name = request.match_info["project_name"]
    project = get_project_name(session, project_name)
    return web.Response(text=f"{project}")

