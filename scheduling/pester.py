from mail import send_user_email
from permissions import get_users_with_permission


async def pester(app, deadline, delta_time):
    groups = app["deadlines"][deadline]["pester"]
    template = app["deadlines"][deadline].get("pester_template", "generic")
    users = get_users_with_permission(app, groups)
    pester_content = app["deadlines"][deadline].get("pester_content", "")
    for user in users:
        await send_user_email(app,
                              user,
                              f"pester_{template}",
                              delta_time=delta_time,
                              pester_content=pester_content,
                              deadline_name=deadline)
