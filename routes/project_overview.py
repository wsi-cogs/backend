from db import Project, User
from aiohttp import web
from aiohttp_jinja2 import template
from project import get_most_recent_group, get_group

@template('group_overview.jinja2')
async def group_overview(request):
    """
    Find the correct group and send it to the user.
    Note that this view should be read only to all users.

    :param request:
    :return Response:
    """
    if "group_series" in request.match_info:
        series = request.match_info["group_series"]
        part = request.match_info["group_part"]
        group = get_group(series, part, session=request.app["session"])
    else:
        group = get_most_recent_group(session=request.app["session"])
    if group is None:
        return web.Response(status=404)
    session = request.app["session"]
    projects = session.query(Project).filter_by(group=group.id).all()
    for project in projects:
        project.supervisor_user = session.query(User).filter_by(id=project.supervisor).first()
    session.flush()
    return {"project_list": projects}


async def series_overview(request):
    """
    Find the correct series as well as all groups in that series.
    Note that this view should be read only to all users.

    :param request:
    :return Response:
    """
    return web.Response(text="series_overview")
