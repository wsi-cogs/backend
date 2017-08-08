from aiohttp import web

from db_helper import get_project_id, get_most_recent_group, get_user_id
from permissions import view_only, value_set


@view_only("join_projects")
@value_set("student_choosable")
async def on_submit(request):
    session = request.app["session"]
    cookies = request.cookies
    post = await request.post()
    is_second = post["order"] == "2"
    attrs = ["first_option_id", "second_option_id"]
    project = get_project_id(session, int(post["choice"]))
    if project.group is not get_most_recent_group(session):
        return web.Response(status=403, text="Cannot join legacy projects")
    user = get_user_id(session, cookies)
    setattr(user, attrs[is_second], project.id)
    if getattr(user, attrs[is_second]) == project.id:
        setattr(user, attrs[is_second], None)
    session.commit()
    return web.Response(status=200, text=f"set")
