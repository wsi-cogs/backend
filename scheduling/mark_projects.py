from datetime import datetime, timedelta
from typing import List

from aiohttp.web import Application

import scheduling.deadlines
from db_helper import get_user_id, get_project_id, should_pester_feedback
from mail import send_user_email


async def mark_project(app: Application, to: List[int], project_id: int, late_time: int=0) -> None:
    assert isinstance(project_id, int)
    assert len(to) == 1
    to = to[0]
    assert isinstance(to, int)
    session = app["session"]
    user = get_user_id(app, user_id=to)
    project = get_project_id(session, project_id)
    if not should_pester_feedback(project, user.id):
        return
    await send_user_email(app,
                          user,
                          "student_uploaded",
                          project=project,
                          late_time=late_time)
    #TODO: Change to days
    deadline = datetime.now() + timedelta(seconds=app["misc_config"]["mark_late_time"])
    scheduling.deadlines.schedule_deadline(app=app,
                                           group=project.group,
                                           deadline_id="marking_complete",
                                           time=deadline,
                                           unique=f"{user.id}_{project_id}",
                                           to=[user.id],
                                           project_id=project_id,
                                           late_time=late_time+1)
