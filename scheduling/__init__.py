from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from scheduling.deadlines import deadline_scheduler
from datetime import datetime, timedelta


def setup(app):
    jobstore = SQLAlchemyJobStore(engine=app["db"])
    jobstores = {"default": jobstore}
    scheduler = AsyncIOScheduler(jobstores=jobstores)

    scheduler.start()
    scheduler.print_jobs()
    # TODO: Remove
    scheduler.remove_all_jobs()
    app["scheduler"] = scheduler

    scheduler.add_job(deadline_scheduler,
                      "date",
                      id="student_invite",
                      args=("student_invite",),
                      run_date=datetime.now()+timedelta(seconds=10))
