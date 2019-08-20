"""
Copyright (c) 2019 Genome Research Ltd.

Authors:
* Josh Holland <jh36@sanger.ac.uk>

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

import unittest
from unittest.mock import call, MagicMock
from hypothesis import assume, given, reproduce_failure, settings
from hypothesis.strategies import dates, datetimes, integers, just, one_of

from datetime import date, datetime, timedelta
from itertools import product

from aiohttp import web
# Note: we use aiohttp's AioHTTPTestCase and so on (rather than just mocking
# the request) because the permissions checking expects the authentication
# middleware to exist, and it's probably less pain to set up the application
# "for real" than it is to mock everything related to authentication...
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from asyncio import Future

import cogs
import cogs.routes
from cogs.middlewares.auth.dummy import DummyAuthenticator
from cogs.db.interface import Database, ProjectGroup
from cogs.db.models import User
from cogs.mail import Postman
from cogs.scheduler.scheduler import Scheduler


def future(x):
    f = Future()
    f.set_result(x)
    return f


# The backend deals in datetimes, but only cares about the date.
def todatetime(date):
    return datetime(date.year, date.month, date.day)


class TestRotationApi(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application(middlewares=[cogs.middlewares.auth.middleware])
        app["db"] = db = MagicMock(spec=Database)
        app["auth"] = auth = MagicMock(spec=DummyAuthenticator)
        app["mailer"] = MagicMock(spec=Postman)
        app["scheduler"] = MagicMock(spec=Scheduler)
        cogs.routes.setup(app)
        return app

    @given(
        series=dates(),
        part=integers(1, 3),
        num_users=integers(0, 1000),
        # Only use dates with 4+ digit years, see https://bugs.python.org/issue13305
        initial_deadline=dates(date(1000, 1, 1)),
    )
    @unittest_run_loop
    async def test_rotation_create(self, series, part, num_users, initial_deadline):
        auth, db, mailer, scheduler = (self.app[x] for x in ["auth", "db", "mailer", "scheduler"])
        auth.get_user_from_request.return_value = future(User(user_type="grad_office"))
        db.get_project_group.return_value = None
        db.get_users_by_permission.return_value = [User()] * num_users
        db.add.reset_mock()
        db.commit.reset_mock()
        mailer.send.reset_mock()
        scheduler.schedule_deadline.reset_mock()

        data = {
            "supervisor_submit": todatetime(initial_deadline),
            "student_invite": todatetime(initial_deadline+timedelta(days=1)),
            "student_choice": todatetime(initial_deadline+timedelta(days=2)),
            "student_complete": todatetime(initial_deadline+timedelta(days=3)),
            "marking_complete": todatetime(initial_deadline+timedelta(days=4)),
            "series": series.year,
            "part": part,
        }

        resp = await self.client.post("/api/series", json={**data,
            "supervisor_submit": data["supervisor_submit"].strftime("%Y-%m-%d"),
            "student_invite": data["student_invite"].strftime("%Y-%m-%d"),
            "student_choice": data["student_choice"].strftime("%Y-%m-%d"),
            "student_complete": data["student_complete"].strftime("%Y-%m-%d"),
            "marking_complete": data["marking_complete"].strftime("%Y-%m-%d"),
        })

        # The request should succeed.
        self.assertLess(resp.status, 400)
        # Mail should be sent to each user.
        self.assertEqual(mailer.send.call_count, num_users)
        # All project deadlines should be scheduled.
        self.assertEqual(scheduler.schedule_deadline.call_count, len(cogs.scheduler.constants.GROUP_DEADLINES))
        # The project should be added to the database.
        db.add.assert_called_once()
        db.commit.assert_called()
        rotation = db.add.call_args[0][0]
        for k, v in {**data,
            "student_viewable": False,
            "student_choosable": False,
            "student_uploadable": False,
            "can_finalise": False,
            "read_only": False,
            "manual_supervisor_reminders": None,
        }.items():
            self.assertEqual(getattr(rotation, k), v)

    @given(
        series=dates(),
        part=integers(1, 3),
        num_users=integers(0, 1000),
        orig_deadline=dates(date(1000, 1, 1)),
        new_deadline=dates(date(1000, 1, 1))
    )
    @unittest_run_loop
    async def test_rotation_edit(self, series, part, num_users, orig_deadline, new_deadline):
        auth, db, mailer, scheduler = (self.app[x] for x in ["auth", "db", "mailer", "scheduler"])
        auth.get_user_from_request.return_value = future(User(user_type="grad_office"))
        db.get_project_group.return_value = ProjectGroup(
            supervisor_submit=orig_deadline,
            student_invite=orig_deadline+timedelta(days=1),
            student_choice=orig_deadline+timedelta(days=2),
            student_complete=orig_deadline+timedelta(days=3),
            marking_complete=orig_deadline+timedelta(days=4),
        )
        db.get_users_by_permission.return_value = [User()] * num_users
        db.add.reset_mock()
        db.commit.reset_mock()
        mailer.send.reset_mock()
        scheduler.schedule_deadline.reset_mock()

        resp = await self.client.put(f"/api/series/{series.year}/{part}", json={
            "deadlines": {
                "supervisor_submit": todatetime(new_deadline).strftime("%Y-%m-%d"),
                "student_invite": todatetime(new_deadline+timedelta(days=1)).strftime("%Y-%m-%d"),
                "student_choice": todatetime(new_deadline+timedelta(days=2)).strftime("%Y-%m-%d"),
                "student_complete": todatetime(new_deadline+timedelta(days=3)).strftime("%Y-%m-%d"),
                "marking_complete": todatetime(new_deadline+timedelta(days=4)).strftime("%Y-%m-%d"),
            },
            "attrs": {},
        })

        # The request should succeed.
        self.assertLess(resp.status, 400)
        # The existing project should be looked up.
        db.get_project_group.assert_called_with(series.year, part)
        # The new project should be saved.
        db.commit.assert_called()
        if orig_deadline != new_deadline:
            # Mail should be sent to each user, once per changed deadline
            # (except student_invite).
            self.assertEqual(mailer.send.call_count, num_users * 4)
            # All project deadlines should be scheduled.
            self.assertEqual(scheduler.schedule_deadline.call_count, len(cogs.scheduler.constants.GROUP_DEADLINES))
