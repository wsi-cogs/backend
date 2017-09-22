from aiohttp.web import Application
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scheduling.deadlines import deadline_scheduler
import sys


def setup(app: Application) -> None:
    jobstore = SQLAlchemyJobStore(engine=app["db"])
    jobstores = {"default": jobstore}
    scheduler = AsyncIOScheduler(jobstores=jobstores,
                                 job_defaults={"misfire_grace_time": 31 * 24 * 60 * 60},
                                 timezone=app["misc_config"]["timezone"])

    scheduler.start()
    app["scheduler"] = scheduler
    if "reset_db" in sys.argv:
        scheduler.remove_all_jobs()

    #from db_helper import get_most_recent_group
    #from datetime import datetime, timedelta
    #deadlines.schedule_deadline(app,
    #                            get_most_recent_group(app["session"]),
    #                            "supervisor_submit",
    #                            datetime.now()+timedelta(seconds=15))
