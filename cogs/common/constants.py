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

from typing import List


# Standard permissions
PERMISSIONS:List[str] = [
    "modify_permissions",          # Can modify permissions
    "create_project_groups",       # Can create rotations
    "set_readonly",                # TODO Can set <SOMETHING> read-only
    "create_projects",             # Can create projects
    "review_other_projects",       # Can review other projects
    "join_projects",               # Can join projects
    "view_projects_predeadline",   # TODO Can view projects before their <WHICH?> deadline
    "view_all_submitted_projects"  # Can view all submitted projects
]

# Rotation e-mail invitation template IDs, for students and supervisors
ROTATION_TEMPLATE_IDS:List[str] = [
    "student_invite_1",            # Student invite for rotation 1
    "student_invite_2",            # ...for rotation 2
    "student_invite_3",            # ...for rotation 3
    "supervisor_invite_1",         # Supervisor invite for rotation 1
    "supervisor_invite_2",         # ...for rotation 2
    "supervisor_invite_3"          # ...for -- wait for it! -- rotation 3
]
