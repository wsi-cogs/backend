from collections import defaultdict
from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from db_helper import get_most_recent_group, get_navbar_data
from permissions import get_users_with_permission, view_only, value_set


@value_set("can_finalise")
@view_only("set_readonly")
@template("finalise_choices.jinja2")
async def finalise_choices(request: Request) -> Dict:
    """
    Create a table with users and their choices for projects to join

    :param request:
    :return Response:
    """
    session = request.app["session"]
    group = get_most_recent_group(session)

    project_choice_map = defaultdict(lambda: defaultdict(lambda: []))
    students = []
    for user in get_users_with_permission(request.app, "join_projects"):
        for i, option in enumerate((user.first_option, user.second_option, user.third_option)):
            if option:
                project_choice_map[option.id][i].append(user)
        if user not in students:
            students.append(user)
    for project_id, options in project_choice_map.items():
        for option in options.values():
            option.sort(key=lambda user: user.priority, reverse=True)
        project_choice_map[project_id]["length"] = max(len(option) for option in options.values())
    return {"projects": group.projects,
            "choices": project_choice_map,
            "students": students,
            "cur_option": "finalise_choices",
            **get_navbar_data(request)}


@value_set("can_finalise")
@view_only("set_readonly")
async def on_submit_group(request: Request) -> Response:
    session = request.app["session"]
    post = await request.post()
    group = get_most_recent_group(session)
    for project in group.projects:
        if str(project.id) not in post:
            project.student_id = None
        else:
            project.student_id = int(post[str(project.id)])
    session.commit()
    return web.Response(status=200, text="/finalise_cogs")


@value_set("can_finalise")
@view_only("set_readonly")
async def on_save_group(request: Request) -> Response:
    await on_submit_group(request)
    return web.Response(status=200, text="/finalise_choices")
