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

from datetime import datetime, timedelta
from typing import Callable, Dict, Tuple

from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import User
from cogs.mail import Postman
from cogs.file_handler import FileHandler
from .constants import DEADLINES, MARK_LATE_TIME


def _get_refs(scheduler:"Scheduler") -> Tuple[Database, Postman, FileHandler]:
    """
    Convenience function for getting references from the Scheduler to
    the database, e-mail and file handling interfaces

    :param scheduler:
    :return:
    """
    return scheduler._db, scheduler._mail, scheduler._file_handler


# All job coroutines should have a signature that takes the scheduler
# interface as its first argument, with any number of additional
# positional and keyword arguments, returning nothing. The scheduler
# interface is injected into the coroutine at runtime and provides
# access to the database interface, e-mailing interface and logging.

# FIXME? Wouldn't these be better as methods of Scheduler? Then the
# argument structure would be conventional, rather than this pretence.
# The only "benefit" of having them separated is that they can live here
# in their own module...

async def supervisor_submit(scheduler:"Scheduler") -> None:
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
    db, mail, _ = _get_refs(scheduler)

    group = db.get_most_recent_group()

    supervisors = db.get_users_by_permission("create_project_groups")
    no_students = len(db.get_users_by_permission("join_projects"))

    for user in supervisors:
        mail.send(user, "supervisor_submit_grad_office", group=group, no_students=no_students)


async def student_invite(scheduler:"Scheduler") -> None:
    """
    Set the group's state such that students can join projects and
    e-mail them the invitation to do so

    FIXME Same concern as above regarding student definition

    :param scheduler:
    :return:
    """
    scheduler.log(logging.INFO, "Inviting students to join projects")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_most_recent_group()
    group.student_viewable = True
    group.student_choosable = True
    group.read_only = True

    students = db.get_users_by_permission("join_projects")
    for user in students:
        mail.send(user, f"student_invite_{group.part}", group=group)


async def student_choice(scheduler:"Scheduler") -> None:
    """
    Set the group's state such that project work can be submitted by
    students and e-mail the Graduate Office to remind them to finalise
    the student choices (i.e., who does which project)

    :param scheduler:
    :return:
    """
    scheduler.log(logging.INFO, "Allowing the Graduate Office to finalise projects")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_most_recent_group()
    group.student_choosable = False
    group.student_uploadable = True
    group.can_finalise = True

    grad_office = db.get_users_by_permission("set_readonly")
    for user in grad_office:
        mail.send(user, "can_set_projects", group=group)


async def student_complete(scheduler:"Scheduler") -> None:
    # TODO
    raise NotImplementedError("Deadline job not implemented")


async def marking_complete(scheduler:"Scheduler") -> None:
    # TODO
    raise NotImplementedError("Deadline job not implemented")


async def grace_deadline(scheduler:"Scheduler", project_id:int) -> None:
    """
    TODO Docstring: Why is this deadline set; when is it set; what
    happens when it's triggered?

    :param scheduler:
    :param project_id:
    :return:
    """
    db, mail, file_handler = _get_refs(scheduler)

    project = db.get_project_by_id(project_id)
    project.grace_passed = True

    student_complete_time = datetime(
        year  = project.group.student_complete.year,
        month = project.group.student_complete.month,
        day   = project.group.student_complete.day)

    reference_date = max(datetime.now(), student_complete_time)
    delta = project.group.marking_complete - project.group.student_complete
    deadline = reference_date + max(delta, timedelta(seconds=5))

    for user in filter(None, (project.supervisor, project.cogs_marker)):
        attachments = file_handler.get_files_by_project(project)
        mail.send(user, "student_uploaded", *attachments, project=project)

        scheduler.schedule_deadline(
            deadline,
            "mark_project",
            project.group,
            suffix     = f"{user.id}_{project.id}",
            user_id    = user.id,
            project_id = project.id)


async def pester(scheduler:"Scheduler", deadline:str, delta_time:timedelta, group_series:int, group_part:int, *recipients:int) -> None:
    """
    Remind users about a specific deadline

    FIXME This is particularly messy!

    :param scheduler:
    :param deadline:
    :param delta_time:
    :param group_series:
    :param group_part:
    :param recipients:
    :return:
    """
    db, mail, _ = _get_refs(scheduler)

    # Explicit users (by their ID) or users defined by their permissions
    users = map(db.get_user_by_id, recipients) if recipients \
            else db.get_users_by_permission(*DEADLINES[deadline].pester_permissions)

    group = db.get_project_group(group_series, group_part)

    predicates:Dict[str, Callable[[User], bool]] = {
        "have_uploaded_project": group.can_solicit_project
    }

    predicate = predicates.get(DEADLINES[deadline].pester_predicate,
                               lambda _user: True)

    template = DEADLINES[deadline].pester_template.format(group=group)
    context = {
        "delta_time":     delta_time,
        "pester_content": DEADLINES[deadline].pester_content,
        "deadline_name":  deadline}

    for user in filter(predicate, users):
        mail.send(user, template, **context)


async def mark_project(scheduler:"Scheduler", user_id:int, project_id:int, late_time:int = 0) -> None:
    """
    E-mail a given user when a specific project is submitted and ready
    for marking, if appropriate; scheduling an additional deadline for
    said marking to be completed

    :param scheduler:
    :param user_id:
    :param project_id:
    :param late_time:
    :return:
    """
    db, mail, _ = _get_refs(scheduler)

    user = db.get_user_by_id(user_id)
    project = db.get_project_by_id(project_id)

    if not project.can_solicit_feedback(user):
        scheduler.log(logging.ERROR, f"Project {project_id} cannot solicit feedback from user {user_id}")
        return

    mail.send(user, "student_uploaded", project=project, late_time=late_time)

    scheduler.schedule_deadline(
        datetime.now() + MARK_LATE_TIME,
        "marking_complete",      # FIXME Not implemented
        project.group,
        suffix     = f"{user.id}_{project.id}",
        to         = [user.id],  # FIXME? Why does this need to be contained in a list
        project_id = project.id,
        late_time  = late_time + 1)
