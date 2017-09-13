from aiohttp.web import Application

from db_helper import get_most_recent_group
from mail import send_user_email
from permissions import get_users_with_permission


async def student_invite(app: Application) -> None:
    print("Inviting students")
    session = app["session"]
    group = get_most_recent_group(session)
    group.student_viewable = True
    group.student_choosable = True
    group.read_only = True
    for user in get_users_with_permission(app, "join_projects"):
        await send_user_email(app,
                              user,
                              "invite_sent",
                              group=group)
