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

from cogs.db.models import Project, User


class TestRelationships(unittest.TestCase):
    def test_get_student_projects(self):
        user = User()
        project1 = Project()
        project2 = Project()
        self.assertEqual(user.projects_as_student, [])
        project1.student = user
        self.assertEqual(user.projects_as_student, [project1])
        project2.student = user
        self.assertEqual(user.projects_as_student, [project1, project2])
