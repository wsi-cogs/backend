"""
Copyright (c) 2017, 2018 Genome Research Ltd.

Authors:
* Christopher Harrison <ch12@sanger.ac.uk>
* Simon Beal <sb48@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import atexit
from datetime import date, timedelta, datetime
from typing import ClassVar, List

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.combining import OrTrigger
from pytz import utc

from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import ProjectGroup
from cogs.mail import Postman
from cogs.file_handler import FileHandler
from . import jobs
from .constants import GROUP_DEADLINES, USER_DEADLINES


class Scheduler(logging.LogWriter):
    """ AsyncIO scheduler interface """
    _scheduler:AsyncIOScheduler
    _db:Database
    _mail:Postman
    _file_handler:FileHandler
    proxy:ClassVar["Scheduler"]

    def __init__(self, database:Database, mail:Postman, file_handler:FileHandler) -> None:
        """
        Constructor
        """
        Scheduler.proxy = self
        self._db = database
        self._mail = mail
        self._file_handler = file_handler

        job_defaults = {
            # APScheduler will only fire events that are up to 31 days out of date
            # This should only happen if the program is abandoned for significant periods
            "misfire_grace_time": int(timedelta(days=31).total_seconds())
        }

        jobstores = {
            "default": SQLAlchemyJobStore(engine=database.engine)}

        self._scheduler = AsyncIOScheduler(
            logger=self._logger,
            timezone=utc,
            job_defaults=job_defaults,
            jobstores=jobstores)

        self._scheduler.start()

        for job in self._scheduler.get_jobs():
            self.log(logging.DEBUG, f"name: {job.name}; "
                                    f"id: {job.id}; "
                                    f"trigger: {job.trigger}; "
                                    f"next run: {job.next_run_time}; "
                                    f"handler: {job.func}; "
                                    f"args: {job.args}; "
                                    f"kwargs: {job.kwargs}; "
                                    f"misfire: {job.misfire_grace_time}")

        atexit.register(self._scheduler.shutdown)

    @staticmethod
    async def _job(__deadline:str, *args, **kwargs) -> None:
        """ Wrapper for the scheduled job, injecting itself """
        print(f"Running job: {__deadline}(*{args}, **{kwargs})")
        await getattr(jobs, __deadline)(Scheduler.proxy, *args, **kwargs)

    def reset_all(self) -> None:
        """ Remove all jobs """
        self._scheduler.remove_all_jobs()

    def schedule_deadline(self, when:date, deadline:str, group:ProjectGroup) -> None:
        """
        Schedule a deadline for the project group
        """
        assert deadline in GROUP_DEADLINES

        schedule_time = self.fix_time(when)

        # Main deadline
        job_id = f"{group.series}_{group.part}_{deadline}"
        self.log(logging.DEBUG, f"Scheduling a deadline `{job_id}` to be ran at `{schedule_time}`")
        self._scheduler.add_job(
            self._job,
            trigger = DateTrigger(run_date=schedule_time),
            id = job_id,
            args = (deadline,),
            kwargs = {"rotation_id": group.id},
            replace_existing = True,
        )

        # Pester points
        # The reminder job contains logic to ensure that tasks are only
        # completed if the appropriate conditions are met, otherwise
        # they're effectively no-ops
        if GROUP_DEADLINES[deadline].pester_times:
            self._scheduler.add_job(
                self._job,
                id=f"reminders_for_{job_id}",
                # DateTrigger does not work properly with OrTrigger:
                # https://gitter.im/apscheduler/Lobby?at=5d5e8c707d3c1636411e17f1
                # so we use this ugly hack to make a CronTrigger that
                # does the same thing as a DateTrigger.
                trigger=OrTrigger([
                    CronTrigger(
                        **dict(zip(
                            ["year", "month", "day", "hour", "minute", "second"],
                            (schedule_time - timedelta(days=delta_day)).timetuple()[:6]
                        ))
                    )
                    for delta_day in GROUP_DEADLINES[deadline].pester_times
                ]),
                args=("reminder",),
                kwargs={"deadline": deadline, "rotation_id": group.id},
                replace_existing=True,
                coalesce=True,
            )
        # Remove existing old-style pester jobs
        # TODO: remove this once there are no instances with scheduled pesters
        for delta_day in GROUP_DEADLINES[deadline].pester_times:
            existing_job = self._scheduler.get_job(f"pester_{delta_day}_{job_id}")
            if existing_job is not None:
                self._scheduler.remove_job(f"pester_{delta_day}_{job_id}")

    def schedule_user_deadline(self, when: date, deadline: str, suffix: str, **kwargs):
        assert deadline in USER_DEADLINES
        schedule_time = self.fix_time(when)
        job_id = f"{deadline}_{suffix}"
        self.log(logging.DEBUG, f"Scheduling a user deadline `{job_id}` to be ran at `{schedule_time}`")
        self._scheduler.add_job(self._job,
                                trigger          = DateTrigger(run_date=schedule_time),
                                id               = job_id,
                                args             = (deadline,),
                                kwargs           = kwargs,
                                replace_existing = True)

    def fix_time(self, when: date) -> datetime:
        """
        Given a date, return the actual time the deadline should be scheduled for
        """
        return datetime(
            year=when.year,
            month=when.month,
            day=when.day,
            hour=23,
            minute=59
        )

    def get_job(self, job_id):
        return self._scheduler.get_job(job_id)

