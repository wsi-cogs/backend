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
from aiohttp.web_exceptions import HTTPForbidden

from cogs.common.constants import PERMISSIONS
from cogs.security.middleware import permit, permit_when_set
from cogs.security.roles import zero, grad_office, student, supervisor, cogs_member

from test.async import async_test


async def noop(request): pass


class StrippedUser:
    def __init__(self, role):
        self.role = role


class TestMiddleware(unittest.TestCase):
    def setUp(self):
        self.no_user = {}
        self.z_user = {"user": StrippedUser(zero)}
        self.go_user = {"user": StrippedUser(grad_office)}
        self.st_user = {"user": StrippedUser(student)}
        self.su_user = {"user": StrippedUser(supervisor)}
        self.c_user = {"user": StrippedUser(cogs_member)}
        self.all_user = {"user": StrippedUser(grad_office | student | supervisor | cogs_member)}


    @async_test
    async def test_permit_construction(self):
        self.assertRaises(AssertionError, permit, "test")
        self.assertRaises(AssertionError, permit)
        for perm in PERMISSIONS:
            permit(perm)
            permit(perm, "set_readonly")

    @async_test
    async def test_permit_no_perms(self):
        for perm in PERMISSIONS:
            fn = permit(perm)(noop)
            with self.assertRaises(HTTPForbidden):
                await fn(self.no_user)

    @async_test
    async def test_permit_all_perms(self):
        for perm in PERMISSIONS:
            await permit(perm)(noop)(self.all_user)


if __name__ == "__main__":
    unittest.main()
