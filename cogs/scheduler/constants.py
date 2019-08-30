"""
Copyright (c) 2017, 2018 Genome Research Ltd.

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

from datetime import timedelta
from typing import Dict, List

from .model import Deadline


# FIXME These jobs aren't very well named; they should be descriptive
# with regard to their action

# Schedulable deadlines
# NB: the `name`s here are user-facing -- they're the only user-visible
# description of what each deadline means.
GROUP_DEADLINES:Dict[str, Deadline] = {
    "supervisor_submit": Deadline(
        name               = "Supervisors should submit projects by:",
        pester_times       = [1, 7],
        pester_template    = "supervisor_invite",
        pester_permissions = ["create_projects"],
        pester_predicate   = lambda user, rotation, **_: rotation.can_solicit_project(user)
    ),

    "student_invite": Deadline(
        name               = "Students are invited on:",
        pester_times       = [1, 7],
        pester_permissions = ["create_project_groups"],
        pester_content     = "make sure there are enough projects for students"),

    "student_choice": Deadline(
        name               = "Students must choose projects by:",
        pester_permissions = ["join_projects"]),

    "student_complete": Deadline(
        name               = "Students must upload reports by:",
        pester_times       = [1, 7, 14],
        pester_permissions = ["join_projects"],
        pester_content     = "upload your project"),

    "marking_complete": Deadline(
        # NB: no reminders here because the project marking reminders
        # are handled specially -- see cogs.scheduler.jobs.mark_project
        # (and grace_deadline, which schedules the initial one).
        name               = "Markers should submit feedback by:",
        pester_content     = "submit feedback for the project you're marking"),
}

USER_DEADLINES = {
    "grace_deadline": Deadline(
        # TODO
        name               = "Deadline for student to reupload project"),

    "reminder": Deadline(
        # TODO
        name               = "When the system should consider sending out bulk email"),

    "mark_project": Deadline(
        # TODO
        name               = "Remind people that there are projects to be marked.")
}

DEADLINES = {**GROUP_DEADLINES, **USER_DEADLINES}

# How long to wait after the deadline before pestering supervisors and between pesters
MARK_LATE_TIME = timedelta(days=7)

# How much time users have after the deadline to re-upload changes
SUBMISSION_GRACE_TIME = timedelta(days=3)
