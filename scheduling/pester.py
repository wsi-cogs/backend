from typing import Optional, List

from db_helper import get_user_id, should_pester_upload
from mail import send_user_email
from permissions import get_users_with_permission


async def pester(app, deadline, delta_time, users: Optional[List[int]]=None):
    if users is None:
        groups = app["deadlines"][deadline]["pester"]
        users = get_users_with_permission(app, groups)
    else:
        session = app["session"]
        users = (get_user_id(session=session, user_id=user_id) for user_id in users)
    if deadline not in app["deadlines"]:
        return
    func_name = app["deadlines"][deadline].get("predicate", "true")
    func = funcs[func_name]
    template = app["deadlines"][deadline].get("pester_template", "generic")
    pester_content = app["deadlines"][deadline].get("pester_content", "")
    for user in users:
        if func(app, user):
            await send_user_email(app,
                                  user,
                                  f"pester_{template}",
                                  delta_time=delta_time,
                                  pester_content=pester_content,
                                  deadline_name=deadline)


funcs = {"true": lambda app, user: True,
         "have_uploaded_project": should_pester_upload}
