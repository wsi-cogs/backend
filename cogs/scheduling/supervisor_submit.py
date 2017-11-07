from aiohttp.web import Application

from cogs.db.functions import get_most_recent_group
from mail import send_user_email
from permissions import get_users_with_permission


async def supervisor_submit(app: Application) -> None:
    print("Reminding grad office")
    session = app["session"]
    no_students = len(get_users_with_permission(app, "join_projects"))
    group = get_most_recent_group(session)
    for user in get_users_with_permission(app, "create_project_groups"):
        await send_user_email(app,
                              user,
                              "supervisor_submit_grad_office",
                              group=group,
                              no_students=no_students)
