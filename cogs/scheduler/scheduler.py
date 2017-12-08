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
from datetime import datetime, timezone, timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

import cogs.scheduler.jobs as jobs
from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import ProjectGroup
from cogs.email import Postman
from .constants import DEADLINES


class Scheduler(logging.LogWriter):
    """ AsyncIO scheduler interface """
    _scheduler:AsyncIOScheduler
    _db:Database
    _mail:Postman

    def __init__(self, database:Database, mail:Postman) -> None:
        """
        Constructor

        :param database:
        :param mail:
        :return:
        """
        self._db = database
        self._mail = mail

        job_defaults = {
            # FIXME? 31 days seems a bit much...
            "misfire_grace_time": int(timedelta(days=31).total_seconds())}

        jobstores = {
            "default": SQLAlchemyJobStore(engine=database.engine)}

        self._scheduler = AsyncIOScheduler(
            logger=self._logger,
            timezone=timezone.utc,
            job_defaults=job_defaults,
            jobstores=jobstores)

        self._scheduler.start()
        atexit.register(self._scheduler.shutdown)

    async def _job(self, deadline:str, *args, **kwargs) -> None:
        """ Wrapper for the scheduled job, injecting itself """
        # FIXME Will this actually work, or will it break APScheduler's
        # serialisability assumptions?...
        await getattr(jobs, deadline)(self, *args, **kwargs)

    def reset_all(self) -> None:
        """ Remove all jobs """
        self._scheduler.remove_all_jobs()

    def schedule_deadline(self, when:datetime, deadline:str, group:ProjectGroup, suffix:str, *args, **kwargs) -> None:
        """
        Schedule a deadline for the project group

        :param when:
        :param deadline:
        :param group:
        :param suffix:
        :return:
        """
        assert deadline in DEADLINES

        # Main deadline
        job_id = f"{group.series}_{group.part}_{deadline}_{suffix}"
        self._scheduler.add_job(self._job,
            trigger          = DateTrigger(run_date=when.astimezone(timezone.utc)),
            id               = job_id,
            args             = (deadline, *args),
            kwargs           = kwargs,
            replace_existing = True)

        # Pester points
        # The pester job contains logic to ensure that tasks are only
        # completed if the appropriate conditions are met, otherwise
        # they're effectively no-ops
        recipient = kwargs.get("to")
        for delta_day in DEADLINES[deadline].pester_times:
            pester_job_id = f"pester_{delta_day}_{job_id}"
            pester_time = when - timedelta(days=delta_day)
            self._scheduler.add_job(self._job,
                trigger          = DateTrigger(run_date=pester_time.astimezone(timezone.utc)),
                id               = pester_job_id,
                args             = ("pester", deadline, delta_day, group.series, group.part, recipient),
                replace_existing = True)


# FIXME Can this be homogenised into the above interface?...

# def add_grace_deadline(scheduler: AsyncIOScheduler, project_id: int, time: datetime):
#     assert isinstance(project_id, int)
#     scheduler.add_job(deadline_scheduler,
#                       "date",
#                       id=f"grace_deadline_{project_id}",
#                       args=("grace_deadline", project_id),
#                       run_date=time)
