from aiohttp import web
from db import Project


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
    project = session.query(Project).filter_by(title=project_name).first()
    return web.Response(text=f"{project}")

