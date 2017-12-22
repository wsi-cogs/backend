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
from unittest.mock import MagicMock, patch

from test.async import async_test

from cogs.db.models import User, ProjectGroup

from cogs.scheduler.jobs import supervisor_submit, student_invite


class TestScheduler(unittest.TestCase):
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
        self.assertTrue(empty_group.read_only)


if __name__ == "__main__":
    unittest.main()
