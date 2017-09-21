from typing import Dict

from aiohttp.web_request import Request
from aiohttp_jinja2 import template

from db_helper import get_projects_supervisor, get_user_id, get_student_projects, get_navbar_data, get_projects_cogs, \
    set_project_can_mark, set_group_attributes, sort_by_attr, get_user_cookies
from permissions import get_user_permissions


@template("user_page.jinja2")
async def user_page(request: Request) -> Dict:
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
    user = get_user_id(request.app, cookies)
    rtn = {
        "user": user,
        "cur_option": "cogs",
        **get_navbar_data(request)
    }
    if user:
        rtn["first_option"] = user.first_option
        rtn["second_option"] = user.second_option
        rtn["third_option"] = user.third_option
    permissions = get_user_permissions(request.app, user)
    if "review_other_projects" in permissions:
        rtn["review_list"] = series_list = get_projects_cogs(request.app, cookies)
        for series in series_list:
            for project in series:
                set_project_can_mark(request.app, cookies, project)
            sort_by_attr(series, "can_mark")
    if "join_projects" in permissions:
        rtn["project_list"] = get_student_projects(request.app, cookies)
    if "create_projects" in permissions:
        rtn["series_list"] = series_list = get_projects_supervisor(session, get_user_cookies(request.app, request.cookies))
        for series in series_list:
            set_group_attributes(request.app, cookies, series)
    return rtn
