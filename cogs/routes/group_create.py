from datetime import datetime, date
from typing import Dict, Union

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from cogs.db.models import ProjectGroup
from cogs.db.functions import get_most_recent_group, get_series, get_navbar_data
from mail import send_user_email
from permissions import view_only, get_users_with_permission
from scheduling.deadlines import schedule_deadline


@template("group_create.jinja2")
@view_only("create_project_groups")
async def group_create(request: Request) -> Union[Dict, Response]:
    """
    Show the form for creating a new group
    This view should only be allowed if the user has 'create_project_groups'

    :param request:
    :return:
    """
    most_recent = get_most_recent_group(request.app["session"])
    series, part = get_new_series_part(most_recent)
    if most_recent.student_choice >= date.today():
        return web.Response(status=403, text="Can't create rotation now, current one is still in student choice phase")
    return {"group": {"part": part},
            "deadlines": request.app["config"]["deadlines"],
            "cur_option": "create_rotation",
            **get_navbar_data(request)}


@view_only("create_project_groups")
async def on_create(request: Request) -> Response:
    """
    Create a new project group
    This view should only be allowed if the user has 'create_project_groups'

    :param request:
    :return:
    """
    session = request.app["session"]
    most_recent = get_most_recent_group(session)
    series, part = get_new_series_part(most_recent)
    post = await request.post()

    if __debug__:
        for deadline in request.app["config"]["deadlines"].keys():
            assert deadline in post and post[deadline], f"The {deadline} deadline was not set"

    deadlines = {deadline: datetime.strptime(post[deadline], "%d/%m/%Y")
                 for deadline in request.app["config"]["deadlines"].keys()}

    group = ProjectGroup(series=series,
                         part=part,
                         read_only=False,
                         can_finalise=False,
                         **deadlines)
    session.add(group)
    most_recent.read_only = True
    session.commit()
    for id, time in deadlines.items():
        schedule_deadline(request.app, group, id, time)
    return web.Response(status=200, text="/")


@view_only("create_project_groups")
async def on_modify(request: Request) -> Response:
    """
    Modify the most recent project group
    This view should only be allowed if the user has 'create_project_groups'

    :param request:
    :return:
    """
    session = request.app["session"]
    part = int(request.match_info["group_part"])
    most_recent = get_most_recent_group(session)
    series = get_series(session, series=most_recent.series)
    group = next(group for group in series if group.part == part)
    post = await request.post()
    for key, value in post.items():
        time = datetime.strptime(value, "%d/%m/%Y").date()
        if key == "supervisor_submit" and time != group.supervisor_submit:
            for supervisor in get_users_with_permission(request.app, "create_projects"):
                await send_user_email(request.app,
                                      supervisor,
                                      f"supervisor_invite_{group.part}",
                                      new_deadline=time,
                                      extension=True)
        setattr(group, key, time)
        if time > date.today():
            schedule_deadline(request.app, group, key, time)
        if key == "student_choice":
            group.student_choosable = time > date.today()
    session.commit()
    return web.Response(status=200, text="/")


def get_new_series_part(group: ProjectGroup):
    series = group.series + group.part // 3
    part = (group.part % 3) + 1
    return series, part
