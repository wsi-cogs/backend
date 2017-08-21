from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scheduling.deadlines import deadline_scheduler


def setup(app):
    jobstore = SQLAlchemyJobStore(engine=app["db"])
    jobstores = {"default": jobstore}
    scheduler = AsyncIOScheduler(jobstores=jobstores)

    scheduler.start()
    scheduler.print_jobs()
    # TODO: Remove
    scheduler.remove_all_jobs()
    app["scheduler"] = scheduler