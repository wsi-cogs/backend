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
from io import BytesIO
from itertools import product

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from asyncio import Future

import cogs
import cogs.routes
from cogs.auth.dummy import DummyAuthenticator
from cogs.db.interface import Database
from cogs.db.models import Project, User
from cogs.file_handler import FileHandler
from cogs.mail import Postman
from cogs.scheduler.scheduler import Scheduler


def future(x):
    f = Future()
    f.set_result(x)
    return f


class TestProjectsApi(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application(middlewares=[cogs.auth.middleware])
        app["db"] = db = MagicMock(spec=Database)
        app["auth"] = auth = MagicMock(spec=DummyAuthenticator)
        app["mailer"] = MagicMock(spec=Postman)
        app["scheduler"] = MagicMock(spec=Scheduler)
        app["file_handler"] = MagicMock(spec=FileHandler)
        cogs.routes.setup(app)
        return app

    @given(student_id=integers(), user_id=integers(), project_id=integers())
    @unittest_run_loop
    async def test_upload_incorrect_user(self, student_id, user_id, project_id):
        assume(user_id != student_id)
        auth, db = (self.app[x] for x in ["auth", "db"])
        user = User(id=user_id, user_type="student")
        student = User(id=student_id, user_type="student")
        auth.get_user_from_request.return_value = future(user)
        db.get_project_by_id.return_value = Project(id=project_id, student=student)

        resp = await self.client.put(f"/api/projects/{project_id}/file", data={"file": BytesIO(b"")})

        self.assertEqual(resp.status, 403)
