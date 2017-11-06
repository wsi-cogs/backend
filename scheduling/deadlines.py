from datetime import timedelta, datetime
from typing import Any

import __main__
from aiohttp.web import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import ProjectGroup
from scheduling.supervisor_submit import supervisor_submit
from scheduling.grace_deadline import grace_deadline
from scheduling.mark_projects import mark_project
from scheduling.pester import pester
from scheduling.student_choice import student_choice
from scheduling.student_invite import student_invite


async def deadline_scheduler(deadline: str, *args, **kwargs) -> None:
    await func_dict.get(deadline, undefined_deadline)(__main__.app, *args, **kwargs)


def schedule_deadline(app: Application, group: ProjectGroup, deadline_id: str, time: datetime, unique: Any="", *args, **kwargs) -> None:
    scheduler = app["scheduler"]
    pester_dates = app["config"]["deadlines"][deadline_id].get("pester_time", [])
    scheduler.add_job(deadline_scheduler,
                      "date",
                      id=f"{group.series}_{group.part}_{deadline_id}_{unique}",
                      args=(deadline_id, *args),
                      kwargs=kwargs,
                      run_date=time,
                      replace_existing=True)
    to = kwargs.get("to", None)
    for delta_day in pester_dates:
        scheduler.add_job(deadline_scheduler,
                          "date",
                          id=f"pester_{delta_day}_{group.series}_{group.part}_{deadline_id}_{unique}",
                          args=("pester", deadline_id, delta_day, group.part, to),
                          run_date=time - timedelta(days=delta_day),
                          replace_existing=True)



def add_grace_deadline(scheduler: AsyncIOScheduler, project_id: int, time: datetime):
    assert isinstance(project_id, int)
    scheduler.add_job(deadline_scheduler,
                      "date",
                      id=f"grace_deadline_{project_id}",
                      args=("grace_deadline", project_id),
                      run_date=time)


async def undefined_deadline(app: Application, *args, **kwargs):
    print(f"undefined deadline with args: {args}, {kwargs}")


func_dict = {
    "supervisor_submit": supervisor_submit,
    "student_invite": student_invite,
    "student_choice": student_choice,
    "grace_deadline": grace_deadline,
    "pester": pester,
    "mark_project": mark_project
}
