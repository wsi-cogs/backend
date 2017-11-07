import os
from datetime import datetime, timedelta

import aiofiles
from aiohttp.web import Application

import routes.student_upload as student_upload
import scheduling.deadlines
from cogs.db.functions import get_project_id
from mail import send_user_email


async def grace_deadline(app: Application, project_id: int) -> None:
    assert isinstance(project_id, int)
    session = app["session"]
    project = get_project_id(session, project_id)
    project.grace_passed = True
    for user in (project.supervisor, project.cogs_marker):
        if user:
            attachments = student_upload.get_stored_paths(project)
            kwargs = {"attachments": {}}
            for path in attachments:
                async with aiofiles.open(path, "rb") as f_obj:
                    await f_obj.seek(0, 2)
                    if await f_obj.tell() < app["config"]["misc"]["max_filesize"]:
                        await f_obj.seek(0)
                        kwargs["attachments"][f"{project.student.name}_{os.path.basename(path)}"] = await f_obj.read()
            await send_user_email(app,
                                  user,
                                  "student_uploaded",
                                  project=project,
                                  user=user,
                                  **kwargs)
            student_complete_time = datetime(year=project.group.student_complete.year,
                                             month=project.group.student_complete.month,
                                             day=project.group.student_complete.day)
            reference_date = max(datetime.now(), student_complete_time)
            delta = project.group.marking_complete - project.group.student_complete
            delta = max(delta, timedelta(seconds=5))
            deadline = reference_date + delta
            scheduling.deadlines.schedule_deadline(app=app,
                                                   group=project.group,
                                                   deadline_id="mark_project",
                                                   time=deadline,
                                                   unique=f"{user.id}_{project_id}",
                                                   to=[user.id],
                                                   project_id=project_id)
