"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
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

from typing import Tuple

from cogs.db.interface import Database
from cogs.email import Postman
from .scheduler import Scheduler


def _get_refs(scheduler:Scheduler) -> Tuple[Database, Postman]:
    """
    Convenience function for getting references from the Scheduler to
    the database and e-mailing interfaces

    :param scheduler:
    :return:
    """
    return scheduler._db, scheduler._mail


# All job coroutines should have a signature that takes the scheduler
# interface as its first argument, with any number of additional
# positional and keyword arguments, returning nothing. The scheduler
# interface is injected into the coroutine at runtime and provides
# access to the database interface, e-mailing interface and logging.

# FIXME? Wouldn't these be better as methods of Scheduler? Then the
# argument structure would be conventional, rather than this pretence.
# The only "benefit" of having them separated is that they can live here
# in their own module...

async def supervisor_submit(scheduler:Scheduler) -> None:
    raise NotImplementedError("...")


async def student_invite(scheduler:Scheduler) -> None:
    raise NotImplementedError("...")


async def student_choice(scheduler:Scheduler) -> None:
    raise NotImplementedError("...")


async def grace_deadline(scheduler:Scheduler) -> None:
    raise NotImplementedError("...")


async def pester(scheduler:Scheduler) -> None:
    raise NotImplementedError("...")


async def mark_project(scheduler:Scheduler) -> None:
    raise NotImplementedError("...")
