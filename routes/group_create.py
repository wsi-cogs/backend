from datetime import datetime

from aiohttp import web
from aiohttp_jinja2 import template

from db import ProjectGroup
from db_helper import get_most_recent_group
from permissions import view_only
from scheduling.deadlines import deadline_scheduler


@template("group_create.jinja2")
@view_only("create_project_groups")
async def group_create(request):
    """
    Show the form for creating a new group
    This view should only be allowed if the user has 'create_project_groups'

    :param request:
    :return:
    """
    return {"group": None, "deadlines": request.app["deadlines"]}


@view_only("create_project_groups")
async def on_create(request):
    """
    Create a new project group
    This view should only be allowed if the user has 'create_project_groups'

    :param request:
    :return:
    """
    session = request.app["session"]
    scheduler = request.app["scheduler"]
    most_recent = get_most_recent_group(session)
    series = most_recent.series + most_recent.part // 3
    part = (most_recent.part % 3) + 1
    post = await request.post()
    deadlines = {key: datetime.strptime(value, "%d/%m/%Y") for key, value in post.items()}
    group = ProjectGroup(series=series,
                         part=part,
                         read_only=False,
                         **deadlines)
    scheduler.remove_all_jobs()
    for id, time in deadlines.items():
        scheduler.add_job(deadline_scheduler,
                          "date",
                          id=id,
                          args=(id,),
                          run_date=time)
    session.add(group)
    most_recent.read_only = True
    session.commit()
    return web.Response(status=200, text="/")


@view_only("modify_project_groups")
async def on_modify(request):
    """
    Modify the most recent project group
    This view should only be allowed if the user has 'modify_project_groups'

    :param request:
    :return:
    """
    session = request.app["session"]
    most_recent = get_most_recent_group(session)
    post = await request.post()
    for key, value in post.items():
        setattr(most_recent, key, datetime.strptime(value, "%d/%m/%Y"))
    session.commit()
    return web.Response(status=200, text="/")
