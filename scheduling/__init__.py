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
    app["scheduler"] = scheduler

    scheduler.add_job(deadline_scheduler,
                      "date",
                      args=("test2",),
                      run_date=datetime.now()+timedelta(seconds=1))