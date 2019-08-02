"""
Copyright (c) 2017, 2018 Genome Research Ltd.

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

from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Tuple

from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import User
from cogs.mail import Postman
from cogs.file_handler import FileHandler
from .constants import GROUP_DEADLINES, MARK_LATE_TIME


def _get_refs(scheduler:"Scheduler") -> Tuple[Database, Postman, FileHandler]:
    """
    Convenience function for getting references from the Scheduler to
    the database, e-mail and file handling interfaces
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
    E-mail the grad office to remind them to submit at least as many
    projects as there are students once the project submission deadline
    has passed

    FIXME This defines students as users who can join projects. This
    permission-based approach would need to be carefully curated by the
    grad office to ensure students from previous years (i.e., who've
    completed to process) aren't caught in subsequent years.
    """
    scheduler.log(logging.INFO, "Reminding grad office to submit projects")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_most_recent_group()

    grad_office_users = db.get_users_by_permission("create_project_groups")
    no_students = len(db.get_users_by_permission("join_projects"))

    for user in grad_office_users:
        mail.send(user, "supervisor_submit_grad_office", group=group, no_students=no_students)


async def student_invite(scheduler:"Scheduler") -> None:
    """
    Set the group's state such that students can join projects and
    e-mail them the invitation to do so

    FIXME Same concern as above regarding student definition
    """
    scheduler.log(logging.INFO, "Inviting students to join projects")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_most_recent_group()
    group.student_viewable = True
    group.student_choosable = True

    students = db.get_users_by_permission("join_projects")
    for user in students:
        mail.send(user, f"student_invite_{group.part}", group=group)


async def student_choice(scheduler:"Scheduler") -> None:
    """
    Set the group's state such that project work can be submitted by
    students and e-mail the Graduate Office to remind them to finalise
    the student choices (i.e., who does which project)
    """
    scheduler.log(logging.INFO, "Allowing the Graduate Office to finalise projects")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_most_recent_group()
    group.student_choosable = False
    group.student_uploadable = True
    group.can_finalise = True
    group.read_only = True

    grad_office = db.get_users_by_permission("set_readonly")
    for user in grad_office:
        mail.send(user, "can_set_projects", group=group)


async def student_complete(scheduler:"Scheduler", *args, **kawrgs) -> None:
    pass


async def marking_complete(scheduler:"Scheduler", *args, **kwargs) -> None:
    pass


async def grace_deadline(scheduler:"Scheduler", project_id:int) -> None:
    """
    Set the project's grace upload period as up, making it so the project can no longer
    be re-uploaded.
    This deadline is called a fixed amount of time after the deadline for that project.
    An email is sent out to the project supervisor and CoGS marker with a request to
    give out feedback.
    A new deadline is scheduled for both which checks to make sure the project is
    marked on time.
    """
    db, mail, file_handler = _get_refs(scheduler)

    project = db.get_project_by_id(project_id)
    project.grace_passed = True

    student_complete_time = datetime(
        year  = project.group.student_complete.year,
        month = project.group.student_complete.month,
        day   = project.group.student_complete.day)

    # Don't punish supervisors for students being late
    reference_date = max(datetime.now(), student_complete_time)
    delta = project.group.marking_complete - project.group.student_complete
    # This is just for testing purposes but is fine to have anyway
    deadline = scheduler.fix_time(reference_date + max(delta, timedelta(seconds=5)))

    for user in filter(None, (project.supervisor, project.cogs_marker)):
        # Send an email to the project supervisor and cogs member
        attachment = file_handler.get_filename_for_project(project)
        mail.send(user, "student_uploaded", attachment, project=project)

        # And prepare to send them emails asking them to mark it
        scheduler.schedule_user_deadline(
            deadline,
            "mark_project",
            f"{user.id}_{project.id}",
            user_id    = user.id,
            project_id = project.id)


# TODO: once there are no instances with an old-style pester scheduled, this job can be removed.
async def pester(scheduler: "Scheduler", deadline: str, delta_time: int, group_series: int, group_part: int, *recipients: int) -> None:
    return reminder(scheduler, deadline, group_series, group_part, *recipients)


async def reminder(scheduler: "Scheduler", deadline: str, group_series: int, group_part: int, *recipients: int) -> None:
    """
    Remind users about a specific deadline
    """
    db, mail, _ = _get_refs(scheduler)

    # Explicit users (by their ID) or users defined by their permissions
    if recipients:
        users: List[User] = list(filter(None, (db.get_user_by_id(uid) for uid in recipients)))
    else:
        users = db.get_users_by_permission(*GROUP_DEADLINES[deadline].pester_permissions)

    # Get the group we are pestering users about (with a slightly
    # awkward construction to make mypy happy).
    maybe_group = db.get_project_group(group_series, group_part)
    assert maybe_group is not None, \
        f"Reminder fired for {group_series}-{group_part}, which doesn't exist!"
    group = maybe_group

    _predicate = GROUP_DEADLINES[deadline].pester_predicate

    # mypy has poor support for functools.partial, so we don't use it here.
    def predicate(user: User):
        return _predicate(user, rotation=group)

    template = GROUP_DEADLINES[deadline].pester_template.format(group=group)
    delta_time = (getattr(group, deadline) - date.today()).days
    for user in filter(predicate, users):
        mail.send(user,
                  template,
                  delta_time=delta_time,
                  pester_content=GROUP_DEADLINES[deadline].pester_content,
                  deadline_name=deadline)


async def mark_project(scheduler:"Scheduler", user_id:int, project_id:int, late_time:int = 0) -> None:
    """
    E-mail a given user (project marker) when a specific project is submitted and ready
    for marking, if appropriate; scheduling an additional deadline to pester about marking again
    """
    db, mail, _ = _get_refs(scheduler)

    user = db.get_user_by_id(user_id)
    project = db.get_project_by_id(project_id)

    if not project.can_solicit_feedback(user):
        scheduler.log(logging.INFO, f"Project {project_id} cannot solicit feedback from user {user_id}, not pestering")
        return

    mail.send(user, "student_uploaded", project=project, late_time=late_time)

    if date.today() > project.group.marking_complete:
        reschedule_time = datetime.now() + MARK_LATE_TIME
    else:
        reschedule_time = project.group.marking_complete

    scheduler.schedule_user_deadline(
        scheduler.fix_time(reschedule_time),
        "mark_project",
        f"{user.id}_{project.id}",
        user_id    = user_id,
        project_id = project.id,
        late_time  = late_time + 1)
