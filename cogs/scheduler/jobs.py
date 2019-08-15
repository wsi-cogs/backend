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
from typing import List, Tuple, TYPE_CHECKING
from typing_extensions import Protocol

from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import User
from cogs.mail import Postman
from cogs.file_handler import FileHandler
from .constants import GROUP_DEADLINES, MARK_LATE_TIME

if TYPE_CHECKING:
    from .scheduler import Scheduler


class _Job(Protocol):
    async def __call__(self, scheduler: "Scheduler", *, rotation_id: int, project_id: int, user_id: int, deadline: str, recipients: List[int], **kwargs) -> None: ...


def job(fn: _Job) -> _Job:
    return fn


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

@job
async def supervisor_submit(scheduler: "Scheduler", *, rotation_id: int, **kwargs) -> None:
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

    group = db.get_rotation_by_id(rotation_id)

    grad_office_users = db.get_users_by_permission("create_project_groups")
    no_students = len(db.get_users_by_permission("join_projects"))

    for user in grad_office_users:
        mail.send(user, "supervisor_submit_grad_office", group=group, no_students=no_students)


@job
async def student_invite(scheduler: "Scheduler", *, rotation_id: int, **kwargs) -> None:
    """
    Set the group's state such that students can join projects and
    e-mail them the invitation to do so

    FIXME Same concern as above regarding student definition
    """
    scheduler.log(logging.INFO, "Inviting students to join projects")
    db, mail, _ = _get_refs(scheduler)

    rotation = db.get_rotation_by_id(rotation_id)
    assert rotation is not None
    rotation.student_viewable = True
    rotation.student_choosable = True

    students = db.get_users_by_permission("join_projects")
    for user in students:
        mail.send(user, f"student_invite", rotation=rotation)


@job
async def student_choice(scheduler: "Scheduler", *, rotation_id: int, **kwargs) -> None:
    """
    Set the group's state such that project work can be submitted by
    students and e-mail the Graduate Office to remind them to finalise
    the student choices (i.e., who does which project)
    """
    scheduler.log(logging.INFO, "Allowing the Graduate Office to finalise projects")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_rotation_by_id(rotation_id)
    assert group is not None
    group.student_choosable = False
    group.can_finalise = True
    group.read_only = True

    grad_office = db.get_users_by_permission("set_readonly")
    for user in grad_office:
        mail.send(user, "can_set_projects", group=group)


@job
async def student_complete(scheduler: "Scheduler", *, rotation_id: int, **kawrgs) -> None:
    scheduler.log(logging.INFO, "Reminding late-submitting students of the deadline")
    db, mail, _ = _get_refs(scheduler)

    group = db.get_rotation_by_id(rotation_id)
    assert group is not None
    for project in group.projects:
        if project.student and not project.uploaded:
            mail.send(project.student, "late_submission_reminder", project=project)


@job
async def marking_complete(scheduler: "Scheduler", *args, **kwargs) -> None:
    pass


@job
async def grace_deadline(scheduler: "Scheduler", *, project_id: int, **kwargs) -> None:
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
    assert project is not None, f"No such project {project_id}"
    project.grace_passed = True

    assert project.group.student_complete is not None
    assert project.group.marking_complete is not None

    # Usually ≈ student_complete + SUBMISSION_GRACE_TIME.
    today = date.today()
    delta = project.group.marking_complete - project.group.student_complete
    reminder_date = today + delta

    for user in filter(None, (project.supervisor, project.cogs_marker)):
        # Send an email to the project supervisor and cogs member
        attachment = file_handler.get_filename_for_project(project)
        mail.send(user, "student_uploaded", attachment, project=project)

        # And prepare to send them emails asking them to mark it
        scheduler.schedule_user_deadline(
            reminder_date,
            "mark_project",
            f"user={user.id}_project={project.id}",
            user_id    = user.id,
            project_id = project.id)


@job
async def reminder(scheduler: "Scheduler", *, deadline: str, rotation_id: int, **kwargs) -> None:
    """
    Remind users about a specific deadline
    """
    db, mail, _ = _get_refs(scheduler)

    users = db.get_users_by_permission(*GROUP_DEADLINES[deadline].pester_permissions)

    # Get the group we are pestering users about (with a slightly
    # awkward construction to make mypy happy).
    maybe_group = db.get_rotation_by_id(rotation_id)
    assert maybe_group is not None, \
        f"Reminder fired for group {rotation_id}, which doesn't exist!"
    group = maybe_group

    _predicate = GROUP_DEADLINES[deadline].pester_predicate

    # mypy has poor support for functools.partial, so we don't use it here.
    def predicate(user: User):
        return _predicate(user, rotation=group)

    template = GROUP_DEADLINES[deadline].pester_template
    delta_time = (scheduler.fix_time(getattr(group, deadline)) - datetime.now())
    for user in filter(predicate, users):
        mail.send(
            user,
            template,
            delta_time=round(delta_time / timedelta(days=1)),
            pester_content=GROUP_DEADLINES[deadline].pester_content,
            deadline_name=deadline,
            rotation=group,
        )


@job
async def mark_project(scheduler: "Scheduler", *, user_id: int, project_id: int, late_time: int = 0, **kwargs) -> None:
    """
    E-mail a given user (project marker) when a specific project is submitted and ready
    for marking, if appropriate; scheduling an additional deadline to pester about marking again
    """
    db, mail, _ = _get_refs(scheduler)

    user = db.get_user_by_id(user_id)
    assert user is not None, f"No such user {user_id}"
    project = db.get_project_by_id(project_id)
    assert project is not None, f"No such project {project_id}"

    if not project.can_solicit_feedback(user):
        scheduler.log(logging.INFO, f"Project {project_id} cannot solicit feedback from user {user_id}, not pestering")
        return

    mail.send(user, "student_uploaded", project=project, late_time=late_time)

    assert project.group.marking_complete is not None
    if date.today() > project.group.marking_complete:
        reschedule_date = date.today() + MARK_LATE_TIME
    else:
        reschedule_date = project.group.marking_complete

    scheduler.schedule_user_deadline(
        reschedule_date,
        "mark_project",
        f"user={user.id}_project={project.id}",
        user_id    = user_id,
        project_id = project.id,
        late_time  = late_time + 1)
