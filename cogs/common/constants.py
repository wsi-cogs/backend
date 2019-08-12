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

import os.path
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple

# Standard permissions
PERMISSIONS:List[str] = [
    "modify_permissions",          # Can modify permissions
    "create_project_groups",       # Can create rotations
    "set_readonly",                # Can set project groups read-only
    "create_projects",             # Can create projects
    "review_other_projects",       # Can review other projects
    "join_projects",               # Can join projects
    "view_projects_predeadline",   # Can view projects before they're visible to students
    "view_all_submitted_projects"  # Can view all submitted projects
]

class NotificationConfiguration(NamedTuple):
    permission: str
    template: str
    # TODO: if email template variables can ever be type-checked, rewrite this.
    get_kwargs: Callable[..., Dict[str, Any]]

DEADLINE_CHANGE_NOTIFICATIONS = {
    "supervisor_submit": NotificationConfiguration(
        "create_projects",
        "supervisor_invite",
        lambda rotation, **_: {"rotation": rotation},
    ),
    "student_choice": NotificationConfiguration(
        "join_projects",
        "student_invite",
        lambda rotation, **_: {"rotation": rotation},
    ),
    "student_complete": NotificationConfiguration(
        "join_projects",
        "project_selected_student",
        lambda rotation, user, db, **_: {"project": db.get_projects_by_student(user, rotation)},
    ),
}

# Absolute path of the job hazard form
# FIXME? Is this the appropriate place to put this?
JOB_HAZARD_FORM = (
    Path(__file__).parent  # Get the directory containing this file.
    / ".."
    / "mail"
    / "attachments"
    / "new_starter_health_questionnaire_jun_17.docx"
).resolve(strict=True)

# Sanger science programmes
PROGRAMMES:List[str] = [
    "Cancer, Ageing and Somatic Mutation",
    "Cellular Genetics",
    "Human Genetics",
    "Parasites and Microbes"
]

# Grades used in marking, with description
class GRADES(Enum):
    A = "Excellent"
    B = "Good"
    C = "Satisfactory"
    D = "Fail"
