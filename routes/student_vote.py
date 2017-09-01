from aiohttp import web

from db_helper import get_project_id, get_user_id
from permissions import view_only, value_set, can_choose_project


@view_only("join_projects")
@value_set("student_choosable")
async def on_submit(request):
    session = request.app["session"]
    cookies = request.cookies
    post = await request.post()
    option = int(post["order"]) - 1
    attrs = ["first_option_id", "second_option_id", "third_option_id"]
    project = get_project_id(session, int(post["choice"]))
    if not can_choose_project(request.app, cookies, project):
        return web.Response(status=403, text="You cannot choose this project")
    user = get_user_id(session, cookies)
    setattr(user, attrs[option], project.id)
    for attr in set(attrs) - {attrs[option]}:
        if getattr(user, attr) == project.id:
            setattr(user, attr, None)
    session.commit()
    return web.Response(status=200, text="set")
