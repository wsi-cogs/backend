from datetime import datetime, timedelta

import scheduling
from db_helper import get_project_id


def add_grace_deadline(scheduler, project_id, time):
    scheduler.add_job(scheduling.deadline_scheduler,
                      "date",
                      id=f"grace_deadline_{project_id}",
                      args=("grace_deadline", project_id),
                      run_date=datetime.now()+timedelta(seconds=5))


def grace_deadline(app, project_id):
    session = app["session"]
    project = get_project_id(session, project_id)
    project.grace_passed = True
