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
from datetime import date

from cogs.scheduler import Scheduler
from cogs.scheduler.constants import GROUP_DEADLINES


_MOCK_SCHEDULER_ARGS = (MagicMock(),) * 3

@patch("cogs.scheduler.scheduler.AsyncIOScheduler", spec=True)
class TestScheduler(unittest.TestCase):
    def test_constructor(self, mock_scheduler):
        s = Scheduler(*_MOCK_SCHEDULER_ARGS)

        mock_scheduler.assert_called_once()
        s._scheduler.start.assert_called_once()

    def test_schedule_deadline(self, mock_scheduler):
        s = Scheduler(*_MOCK_SCHEDULER_ARGS)
        self.assertRaises(AssertionError, s.schedule_deadline, date.today(), "foobar", None)

        for deadline_id, deadline in GROUP_DEADLINES.items():
            s._scheduler.add_job.reset_mock()
            s.schedule_deadline(date.today(), deadline_id, MagicMock())
            s._scheduler.add_job.assert_called_once()

            s._scheduler.add_job.reset_mock()
            s.schedule_deadline(date.today(), deadline_id, MagicMock(), to="foo@bar")
            calls = s._scheduler.add_job.call_count
            self.assertEqual(calls, 1 + len(deadline.pester_times))


if __name__ == "__main__":
    unittest.main()
