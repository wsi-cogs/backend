"""
Copyright (c) 2017 Genome Research Ltd.

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
DEADLINES:Dict[str, Deadline] = {
    "supervisor_submit": Deadline(
        name               = "Submission deadline for supervisors",
        pester_times       = [1, 7, 14, 21],
        pester_template    = "supervisor_invite_{group_part}",
        pester_predicate   = "have_uploaded_project"),

    "student_invite": Deadline(
        name               = "Date students get invited",
        pester_times       = [1, 7],
        pester_permissions = ["create_project_groups"],
        pester_content     = "make sure there are enough projects for students."),

    "student_choice": Deadline(
        name               = "Deadline for student choices",
        pester_permissions = ["join_projects", "create_project_groups"]),

    "student_complete": Deadline(
        name               = "Deadline for report submission",
        pester_times       = [1, 7, 14],
        pester_permissions = ["join_projects", "create_project_groups"]),

    "marking_complete": Deadline(
        name               = "Deadline for report feedback",
        pester_content     = "submit feedback for the project you're marking"),

    "grace_deadline": Deadline(
        # TODO
        name               = "???"),

    "pester": Deadline(
        # TODO
        name               = "???"),

    "mark_project": Deadline(
        # TODO
        name               = "???")
}

# Late marking time (FIXME better description)
MARK_LATE_TIME = timedelta(days=14)
