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

from typing import List

from .models import Project


# FIXME This module should be removed once all of its parts have been
# moved into more appropriate places. All that currently remains are
# functions that I don't yet know what to do with...


# FIXME This function is dangerous and shouldn't be used. The functions
# used within it have been refactored into model predicate methods
# (i.e., which don't change state). Need to look into how this function
# is used to understand how it can be replaced...

# def set_group_attributes(app, cookies:Cookies, group:Union[ProjectGroup, List[Project]]) -> List[Project]:
#     """
#     Return a list of all the projects in a ProjectGroup
#
#     :param app:
#     :param cookies:
#     :param group:
#     :return:
#     """
#     # TODO Tidy up
#     try:
#         projects = group.projects
#     except AttributeError:
#         projects = group
#
#     for project in projects:
#         set_project_can_mark(app, cookies, project)
#         set_project_can_resubmit(app, cookies, project)
#         set_project_read_only(app, cookies, project)
#     sort_by_attr(projects, "supervisor.name")
#     return sort_by_attr(projects, "can_mark")


# FIXME This function would only ever be needed if sorting is done
# outside of the database; I would guess probably for UI reasons. For
# the time being, I've refactored it so it just returns a list of stably
# sorted projects, rather than sorting the reference and returning the
# sorted list.

def sort_projects_by_attr(projects:List[Project], attr:str) -> List[Project]:
    """
    Sort a list of projects by an attribute of a project

    :param projects:
    :param attr:
    :return:
    """
    return sorted(projects, key=lambda p: getattr(p, attr))
