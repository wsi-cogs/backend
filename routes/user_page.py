from typing import Dict

from aiohttp.web_request import Request
from aiohttp_jinja2 import template

from db_helper import get_most_recent_group, get_projects_supervisor, get_user_id, get_student_projects, \
    get_all_groups, get_projects_cogs, set_project_can_mark, set_group_attributes, sort_by_attr, get_dates_from_group, \
    get_series
from permissions import can_view_group, get_user_permissions


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
    most_recent = get_most_recent_group(session)
    series_groups = get_series(session, most_recent.series)
    user = get_user_id(session, cookies)
    rtn = {
        "can_edit": not most_recent.read_only,
        "deadlines": request.app["deadlines"],
        "display_projects_link": can_view_group(request, most_recent),
        "user": user
    }
    if user:
        rtn["first_option"] = user.first_option
        rtn["second_option"] = user.second_option
        rtn["third_option"] = user.third_option
    permissions = get_user_permissions(request.app, user)
    if "create_projects" in permissions:
        rtn["series_list"] = series_list = get_projects_supervisor(session, int(cookies["user_id"]))
        for series in series_list:
            set_group_attributes(cookies, series)
    if "create_project_groups" in permissions:
        rtn["groups"] = [get_dates_from_group(group) for group in series_groups]
    if "set_readonly" in permissions:
        rtn["show_finalise_choices"] = most_recent.can_finalise
    if "review_other_projects" in permissions:
        rtn["review_list"] = series_list = get_projects_cogs(session, cookies)
        for series in series_list:
            for project in series:
                set_project_can_mark(cookies, project)
            sort_by_attr(series_list, "can_mark")
    if "join_projects" in permissions:
        rtn["project_list"] = get_student_projects(session, cookies)
    if "view_all_submitted_projects" in permissions:
        rtn["series_years"] = sorted({group.series for group in get_all_groups(session)}, reverse=True)
        rtn["rotations"] = sorted((group.part for group in series_groups), reverse=True)
    rtn["permissions"] = permissions
    return rtn
