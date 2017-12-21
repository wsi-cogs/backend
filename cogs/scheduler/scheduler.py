"""
Copyright (c) 2017 Genome Research Ltd.

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
from datetime import date, timedelta
from typing import ClassVar

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
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

        :param database:
        :param mail:
        :param file_handler:
        :return:
        """
        Scheduler.proxy = self
        self._db = database
        self._mail = mail
        self._file_handler = file_handler

        job_defaults = {
            # FIXME? 31 days seems a bit much...
            "misfire_grace_time": int(timedelta(days=31).total_seconds())}

        jobstores = {
            "default": SQLAlchemyJobStore(engine=database.engine)}

        self._scheduler = AsyncIOScheduler(
            logger=self._logger,
            timezone=utc,
            job_defaults=job_defaults,
            jobstores=jobstores)

        self._scheduler.start()
        atexit.register(self._scheduler.shutdown)

    @staticmethod
    async def _job(deadline:str, *args, **kwargs) -> None:
        """ Wrapper for the scheduled job, injecting itself """
        # FIXME Will this actually work, or will it break APScheduler's
        # serialisability assumptions?...
        await getattr(jobs, deadline)(Scheduler.proxy, *args, **kwargs)

    def reset_all(self) -> None:
        """ Remove all jobs """
        self._scheduler.remove_all_jobs()

    def schedule_deadline(self, when:date, deadline:str, group:ProjectGroup, suffix:str="", *args, **kwargs) -> None:
        """
        Schedule a deadline for the project group

        :param when:
        :param deadline:
        :param group:
        :param suffix:
        :return:
        """
        assert deadline in GROUP_DEADLINES

        # Main deadline
        job_id = f"{group.series}_{group.part}_{deadline}_{suffix}"
        self.log(logging.DEBUG, f"Scheduling a deadline `{job_id}` to be ran at `{when}`")
        self._scheduler.add_job(self._job,
            trigger          = DateTrigger(run_date=when),
            id               = job_id,
            args             = (deadline, *args),
            kwargs           = kwargs,
            replace_existing = True)

        # Pester points
        # The pester job contains logic to ensure that tasks are only
        # completed if the appropriate conditions are met, otherwise
        # they're effectively no-ops
        if "to" in kwargs:
            recipient = kwargs["to"]
            for delta_day in GROUP_DEADLINES[deadline].pester_times:
                pester_job_id = f"pester_{delta_day}_{job_id}"
                pester_time = when - timedelta(days=delta_day)
                self._scheduler.add_job(self._job,
                    trigger          = DateTrigger(run_date=pester_time),
                    id               = pester_job_id,
                    args             = ("pester", deadline, delta_day, group.series, group.part, recipient),
                    replace_existing = True)

    def schedule_user_deadline(self, when:date, deadline, suffix, *args, **kwargs):
        assert deadline in USER_DEADLINES
        job_id = f"{deadline}_{suffix}"
        self.log(logging.DEBUG, f"Scheduling a user deadline `{job_id}` to be ran at `{when}`")
        self._scheduler.add_job(self._job,
                                trigger          = DateTrigger(run_date=when),
                                id               = job_id,
                                args             = (deadline, *args),
                                kwargs           = kwargs,
                                replace_existing = True)

    def get_job(self, job_id):
        return self._scheduler.get_job(job_id)

