from datetime import timedelta
from typing import Optional, List

from aiohttp.web import Application

from db_helper import get_user_id, should_pester_upload
from mail import send_user_email
from permissions import get_users_with_permission


async def pester(app: Application, deadline: str, delta_time: timedelta, group_part: int, users: Optional[List[int]]=None) -> None:
    if users is None:
        groups = app["config"]["deadlines"][deadline]["pester"]
        users = get_users_with_permission(app, groups)
    else:
        users = (get_user_id(app, user_id) for user_id in users)
    if deadline not in app["config"]["deadlines"]:
        return
    assert isinstance(group_part, int)

    func_name = app["config"]["deadlines"][deadline].get("predicate", "true")
    func = funcs[func_name]
    template = app["config"]["deadlines"][deadline].get("pester_template", "pester_generic").format(group_part=group_part)
    pester_content = app["config"]["deadlines"][deadline].get("pester_content", "")
    for user in users:
        if func(app, user):
            await send_user_email(app,
                                  user,
                                  template,
                                  delta_time=delta_time,
                                  pester_content=pester_content,
                                  deadline_name=deadline)


funcs = {"true": lambda app, user: True,
         "have_uploaded_project": should_pester_upload}
