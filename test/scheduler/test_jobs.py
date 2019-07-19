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

import unittest
from unittest.mock import MagicMock, patch, call, ANY

from test.async_helper import async_test, AsyncTestCase

from cogs.db.models import User, ProjectGroup, Project

from cogs.scheduler.jobs import supervisor_submit, student_invite, student_choice, grace_deadline, pester, mark_project
import cogs.scheduler.jobs as jobs
from cogs.scheduler.constants import DEADLINES, GROUP_DEADLINES


class TestScheduler(AsyncTestCase):
    @async_test
    async def test_supervisor_submit(self):
        scheduler = MagicMock()
        empty_user = User()
        empty_group = ProjectGroup()
        scheduler._db.get_most_recent_group.return_value = empty_group
        for no_users in range(10):
            scheduler._mail.send.reset_mock()
            scheduler._db.get_users_by_permission.return_value = [empty_user] * no_users
            await supervisor_submit(scheduler)
            calls = scheduler._mail.send.call_count
            self.assertEqual(calls, no_users)
            if no_users != 0:
                scheduler._mail.send.assert_called_with(empty_user,
                                                        "supervisor_submit_grad_office",
                                                        group=empty_group,
                                                        no_students=no_users)

    @async_test
    async def test_student_invite(self):
        scheduler = MagicMock()
        empty_user = User()
        empty_group = ProjectGroup(part="<Hello>")
        scheduler._db.get_most_recent_group.return_value = empty_group
        for no_users in range(10):
            scheduler._mail.send.reset_mock()
            scheduler._db.get_users_by_permission.return_value = [empty_user] * no_users
            await student_invite(scheduler)
            calls = scheduler._mail.send.call_count
            self.assertEqual(calls, no_users)
            if no_users != 0:
                scheduler._mail.send.assert_called_with(empty_user,
                                                        f"student_invite_<Hello>",
                                                        group=empty_group)
        self.assertTrue(empty_group.student_viewable)
        self.assertTrue(empty_group.student_choosable)
        self.assertFalse(empty_group.read_only)

    @async_test
    async def test_student_choice(self):
        scheduler = MagicMock()
        empty_user = User()
        empty_group = ProjectGroup()
        scheduler._db.get_most_recent_group.return_value = empty_group
        for no_users in range(10):
            scheduler._mail.send.reset_mock()
            scheduler._db.get_users_by_permission.return_value = [empty_user] * no_users
            await student_choice(scheduler)
            calls = scheduler._mail.send.call_count
            self.assertEqual(calls, no_users)
            if no_users != 0:
                scheduler._mail.send.assert_called_with(empty_user,
                                                        "can_set_projects",
                                                        group=empty_group)
        self.assertFalse(empty_group.student_choosable)
        self.assertTrue(empty_group.student_uploadable)
        self.assertTrue(empty_group.can_finalise)
        self.assertTrue(empty_group.read_only)

    def test_all_deadlines_exist(self):
        for deadline in DEADLINES:
            self.assertTrue(hasattr(jobs, deadline))

    @patch("cogs.scheduler.jobs.timedelta", spec=True)
    @async_test
    async def test_grace_deadline(self, mock_timedelta):
        mock_timedelta().__gt__.return_value = False
        scheduler = MagicMock()
        supervisor = User(name="Bob")
        cogs_marker = User(name="Sue")
        scheduler._file_handler.get_filename_for_project.return_value = "project-files.zip"
        for s, c in ((None, None), (supervisor, None), (None, cogs_marker), (supervisor, cogs_marker)):
            scheduler._mail.send.reset_mock()
            empty_project = Project(group=MagicMock(),
                                    supervisor=s,
                                    cogs_marker=c)
            scheduler._db.get_project_by_id.return_value = empty_project
            await grace_deadline(scheduler, 0)

            self.assertTrue(empty_project.grace_passed)

            calls = [call(user,
                          "student_uploaded",
                          "project-files.zip",
                          project=empty_project) for user in (s, c) if user]
            scheduler._mail.send.assert_has_calls(calls)

            calls = [call(ANY,
                          "mark_project",
                          f"{user.id}_{empty_project.id}",
                          user_id=user.id,
                          project_id=empty_project.id) for user in (s, c) if user]
            scheduler.schedule_user_deadline.assert_has_calls(calls)

    @async_test
    async def test_pester(self):
        scheduler = MagicMock()

        for deadline_id, deadline in GROUP_DEADLINES.items():
            if deadline.pester_times:
                user = User()
                scheduler._db.get_user_by_id.return_value = user
                empty_group = MagicMock()
                empty_group.part = "test"
                scheduler._db.get_project_group.return_value = empty_group
                await pester(scheduler, deadline_id, None, None, None, None)

                if deadline.pester_predicate == "have_uploaded_project":
                    empty_group.can_solicit_project.assert_called_once()

                scheduler._mail.send.assert_called_with(user,
                                                        deadline.pester_template.format(group=empty_group),
                                                        deadline_name=deadline_id,
                                                        delta_time=None,
                                                        pester_content=deadline.pester_content)

    @patch("cogs.scheduler.jobs.datetime", spec=True)
    @async_test
    async def test_mark_project(self, mock_datetime):
        mock_datetime.date.today().__gt__.return_value = False
        scheduler = MagicMock()

        user = User()
        scheduler._db.get_user_by_id.return_value = user

        project = MagicMock()
        project.can_solicit_feedback.return_value = True
        scheduler._db.get_project_by_id.return_value = project

        await mark_project(scheduler, None, None)

        scheduler._mail.send.assert_called_with(user,
                                                "student_uploaded",
                                                project=project,
                                                late_time=0)

        scheduler.schedule_user_deadline.assert_called_with(ANY,
                                                       "mark_project",
                                                       f"{user.id}_{project.id}",
                                                       user_id=user.id,
                                                       project_id=project.id,
                                                       late_time=1)


if __name__ == "__main__":
    unittest.main()
