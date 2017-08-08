from datetime import date

from aiohttp_jinja2 import template

from db_helper import get_most_recent_group, get_projects_user
from permissions import get_permission_from_cookie, can_view_group


@template("user_page.jinja2")
async def user_page(request):
    """
    Get the page for the user.
    If they own projects, show them including legacy projects.
    If they are part of projects, show them.
    If they are in the process for signing up for projects, put them at the start

    :param request:
    :return:
    """
    cookies = request.cookies
    session = request.app["session"]
    group = get_most_recent_group(session)
    rtn = {"can_edit": not group.read_only,
           "deadlines": request.app["deadlines"],
           "display_projects_link": can_view_group(request, group)}
    if get_permission_from_cookie(cookies, "create_projects"):
        rtn["series_list"] = get_projects_user(request, int(cookies["user_id"]))
    if get_permission_from_cookie(cookies, "modify_project_groups"):
        rtn["group"] = {}
        for column in group.__table__.columns:
            rtn["group"][column.key] = getattr(group, column.key)
            if isinstance(rtn["group"][column.key], date):
                rtn["group"][column.key] = rtn["group"][column.key].strftime("%d/%m/%Y")
    rtn.update(cookies)
    return rtn
