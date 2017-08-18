import os

import aiofiles

import routes.student_upload as student_upload
import scheduling
from db_helper import get_project_id
from mail import send_user_email


def add_grace_deadline(scheduler, project_id, time):
    scheduler.add_job(scheduling.deadline_scheduler,
                      "date",
                      id=f"grace_deadline_{project_id}",
                      args=("grace_deadline", project_id),
                      run_date=time)


async def grace_deadline(app, project_id):
    session = app["session"]
    project = get_project_id(session, project_id)
    project.grace_passed = True
    for user in (project.supervisor, project.cogs_marker):
        if user:
            path = student_upload.get_stored_path(project)
            async with aiofiles.open(path, "rb") as f_obj:
                await send_user_email(app,
                                      user,
                                      "student_uploaded",
                                      attachments={f"{project.student.name}_{os.path.basename(path)}": await f_obj.read()},
                                      project=project)
