"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Christopher Harrison <ch12@sanger.ac.uk>

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

from datetime import timezone, timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from cogs.common.logging import LogWriter
from cogs.db.interface import Database
from cogs.email import Postman


class Scheduler(LogWriter):
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
            "misfire_grace_time": int(timedelta(days=31).total_seconds())}

        jobstores = {
            "default": SQLAlchemyJobStore(engine=database.engine)}

        self._scheduler = AsyncIOScheduler(
            logger=self._logger,
            timezone=timezone.utc,
            job_defaults=job_defaults,
            jobstores=jobstores)

        self._scheduler.start()

    def reset_all(self) -> None:
        """ Remove all jobs """
        self._scheduler.remove_all_jobs()
