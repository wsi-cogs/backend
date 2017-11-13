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

from .type import Role


grad_office = Role(
    modify_permissions          = True,
    create_project_groups       = True,
    set_readonly                = True,
    create_projects             = False,
    review_other_projects       = False,
    join_projects               = False,
    view_projects_predeadline   = True,
    view_all_submitted_projects = True
)

supervisor = Role(
    modify_permissions          = False,
    create_project_groups       = False,
    set_readonly                = False,
    create_projects             = True,
    review_other_projects       = False,
    join_projects               = False,
    view_all_submitted_projects = False
)

cogs_member = Role(
    modify_permissions          = False,
    create_project_groups       = False,
    set_readonly                = False,
    create_projects             = False,
    review_other_projects       = True,
    join_projects               = False,
    view_projects_predeadline   = True,
    view_all_submitted_projects = False
)

student = Role(
    modify_permissions          = False,
    create_project_groups       = False,
    set_readonly                = False,
    create_projects             = False,
    review_other_projects       = False,
    join_projects               = True,
    view_projects_predeadline   = False,
    view_all_submitted_projects = False
)
