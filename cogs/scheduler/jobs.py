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

from cogs.common import logging
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
    """
    E-mail supervisors to remind them to submit at least as many
    projects as there are students once the project submission deadline
    has passed

    FIXME This defines students as users who can join projects. This
    permission-based approach would need to be carefully curated by the
    grad office to ensure students from previous years (i.e., who've
    completed to process) aren't caught in subsequent years.

    :param scheduler:
    :return:
    """
    scheduler.log(logging.INFO, "Reminding supervisors to submit projects")
    db, mail = _get_refs(scheduler)

    group = db.get_most_recent_group()

    supervisors = db.get_users_by_permission("create_project_groups")
    no_students = len(db.get_users_by_permission("join_projects"))

    for user in supervisors:
        mail.send(user, "supervisor_submit_grad_office", group=group, no_students=no_students)


async def student_invite(scheduler:Scheduler) -> None:
    """
    Set the group's state such that students can join projects and
    e-mail them the invitation to do so

    FIXME Same concern as above regarding student definition

    :param scheduler:
    :return:
    """
    scheduler.log(logging.INFO, "Inviting students to join projects")
    db, mail = _get_refs(scheduler)

    group = db.get_most_recent_group()
    group.student_viewable = True
    group.student_choosable = True
    group.read_only = True

    students = db.get_users_by_permission("join_projects")
    for user in students:
        mail.send(user, f"student_invite_{group.part}", group=group)


async def student_choice(scheduler:Scheduler) -> None:
    """
    Set the group's state such that project work can be submitted by
    students and e-mail the Graduate Office to remind them to finalise
    the student choices (i.e., who does which project)

    :param scheduler:
    :return:
    """
    scheduler.log(logging.INFO, "Allowing the Graduate Office to finalise projects")
    db, mail = _get_refs(scheduler)

    group = db.get_most_recent_group()
    group.student_choosable = False
    group.student_uploadable = True
    group.can_finalise = True

    grad_office = db.get_users_by_permission("set_readonly")
    for user in grad_office:
        mail.send(user, "can_set_projects", group=group)


async def grace_deadline(scheduler:Scheduler) -> None:
    """
    TODO Docstring: Why is this deadline set; when is it set; what
    happens when it's triggered?
    """
    raise NotImplementedError("...")


async def pester(scheduler:Scheduler) -> None:
    """
    TODO Docstring: Why is this deadline set; when is it set; what
    happens when it's triggered?
    """
    raise NotImplementedError("...")


async def mark_project(scheduler:Scheduler) -> None:
    """
    TODO Docstring: Why is this deadline set; when is it set; what
    happens when it's triggered?
    """
    raise NotImplementedError("...")
