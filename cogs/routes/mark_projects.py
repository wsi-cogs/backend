from typing import Dict

from aiohttp.web_request import Request
from aiohttp_jinja2 import template

from cogs.db.functions import get_projects_supervisor, get_user_id, get_navbar_data, get_projects_cogs, get_user_cookies, \
    can_provide_feedback
from permissions import get_user_permissions


@template("markable_projects.jinja2")
async def markable_projects(request: Request) -> Dict:
    """
    Get all projects the user can mark

    :param request:
    :return:
    """
    cookies = request.cookies
    session = request.app["session"]
    user = get_user_id(request.app, cookies)
    rtn = {
        "cur_option": "markable_projects",
        "no_projects": "There are no projects you can mark",
        **get_navbar_data(request)
    }
    permissions = get_user_permissions(request.app, user)
    projects = []
    if "review_other_projects" in permissions:
        series_list = get_projects_cogs(request.app, cookies)
        for series in series_list:
            projects.extend(series)

    if "create_projects" in permissions:
        series_list = get_projects_supervisor(session, get_user_cookies(request.app, request.cookies))
        for series in series_list:
            projects.extend(series)

    rtn["project_list"] = [project for project in projects if can_provide_feedback(request.app, cookies, project)]
    return rtn
