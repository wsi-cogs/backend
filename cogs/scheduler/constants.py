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

from typing import Dict, List

# FIXME These don't correspond, neither with each other nor the legacy,
# example configuration...

# FIXME These jobs aren't very well named; they should be descriptive
# with regard to their action

# Schedulable deadlines
DEADLINES:List[str] = [
    "supervisor_submit",
    "student_invite",
    "student_choice",
    "grace_deadline",
    "pester",
    "mark_project"
]

# Pester times (days)
PESTER_TIMES:Dict[str, List[int]] = {
    "supervisor_submit": [1, 7, 14, 21],
    "student_invite":    [1, 7],
    "student_choice":    [],
    "student_complete":  [1, 7, 14],  # FIXME No corresponding deadline
}
