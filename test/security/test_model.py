"""
Copyright (c) 2018 Genome Research Ltd.

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

import unittest

from cogs.security.model import Role, _build_role


class TestModel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.role = _build_role("a", "b")

    def test_repr(self):
        role = self.role(a=True, b=False)
        self.assertEqual(repr(role), "Role(a=True, b=False)")

    def test_bool(self):
        self.assertFalse(bool(self.role(a=False, b=False)))
        self.assertTrue(bool(self.role(a=False, b=True)))
        self.assertTrue(bool(self.role(a=True, b=False)))
        self.assertTrue(bool(self.role(a=True, b=True)))

    def test_eq(self):
        role = self.role(a=True, b=False)
        role2 = self.role(a=True, b=False)
        self.assertEqual(role, role)
        self.assertEqual(role, role2)

        role3 = self.role(a=False, b=False)
        self.assertNotEqual(role, role3)

        role_class_2 = _build_role("a")
        role4 = role_class_2(a=False)
        self.assertNotEqual(role, role4)
        self.assertNotEqual(role3, role4)

    def test_or(self):
        role1 = self.role(a=False, b=False)
        role2 = self.role(a=False, b=True)
        role3 = self.role(a=True, b=False)
        role4 = self.role(a=True, b=True)
        self.assertEqual(role1 | role1, role1)
        self.assertEqual(role1 | role2, role2)
        self.assertEqual(role1 | role3, role3)
        self.assertEqual(role2 | role3, role4)
        self.assertEqual(role4 | role2, role4)
        self.assertEqual(role4 | role3, role4)

    def test_and(self):
        role1 = self.role(a=False, b=False)
        role2 = self.role(a=False, b=True)
        role3 = self.role(a=True, b=False)
        role4 = self.role(a=True, b=True)
        self.assertEqual(role4 & role1, role1)
        self.assertEqual(role4 & role2, role2)
        self.assertEqual(role4 & role3, role3)
        self.assertEqual(role2 & role3, role1)
        self.assertEqual(role4 & role2, role2)
        self.assertEqual(role4 & role3, role3)

    def test_constructor(self):
        self.assertRaises(TypeError, self.role)
        self.assertRaises(TypeError, Role)
        Role(
            modify_permissions=False,
            create_project_groups=False,
            set_readonly=False,
            create_projects=False,
            review_other_projects=False,
            join_projects=False,
            view_projects_predeadline=False,
            view_all_submitted_projects=False)


if __name__ == "__main__":
    unittest.main()
