from collections import defaultdict
from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from db_helper import get_most_recent_group, get_project_id, get_projects_supervisor, get_navbar_data
from mail import send_user_email
from permissions import get_users_with_permission, view_only, value_set


@value_set("can_finalise")
@view_only("set_readonly")
@template('finalise_cogs.jinja2')
async def finalise_cogs(request: Request) -> Dict:
    session = request.app["session"]
    group = get_most_recent_group(session)
    cogs_members = list(get_users_with_permission(request.app, "review_other_projects"))
    return {"projects": [project for project in group.projects if project.student],
            "cogs_members": cogs_members,
            "show_back": True,
            "cur_option": "finalise_choices",
            "use_fluid": True,
            **get_navbar_data(request)}


@value_set("can_finalise")
@view_only("set_readonly")
async def on_submit_cogs(request: Request) -> Response:
    session = request.app["session"]
    supervisors = defaultdict(list)
    group = get_most_recent_group(session)
    for project in group.projects:
        if project.student:
            student = project.student
            project.student_uploadable = True
            try:
                choice = (student.first_option, student.second_option, student.third_option).index(project)
            except ValueError:
                choice = 3
            student.priority += (2 ** choice) - 1
            student.first_option = None
            student.second_option = None
            student.third_option = None
            await send_user_email(request.app, student, "project_selected_student", project=project)
            supervisors[project.supervisor].append(project)
    for project_id, cogs_member_id in (await request.post()).items():
        project = get_project_id(session, int(project_id))
        if cogs_member_id == "-1":
            project.cogs_marker_id = None
        else:
            project.cogs_marker_id = int(cogs_member_id)
    for supervisor in get_users_with_permission(request.app, "create_projects"):
        projects = [project for project in sum(get_projects_supervisor(session, supervisor.id), [])
                    if project.group == group]
        # TODO: Add job hazard form
        if projects:
            await send_user_email(request.app, supervisor, "project_selected_supervisor", projects=projects)
    group.can_finalise = False
    session.commit()
    return web.Response(status=200, text="/")
