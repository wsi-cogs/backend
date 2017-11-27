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

from datetime import date
from typing import List, Dict

from cogs.auth.dummy import DummyAuthenticator
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


# FIXME This belongs in a middleware layer, rather than as part of the
# database interface...

def get_navbar_data(request) -> Dict:
    """
    Get the data that should be in every request

    :param request:
    :return:
    """
    # TODO Tidy up
    session = request.app["session"]
    most_recent = get_most_recent_group(session)
    user = get_user_id(request.app, request.cookies)
    permissions = get_user_permissions(request.app, user)
    root_map = {"join_projects": "My Choices",
                "create_projects": "My Owned Projects",
                "create_project_groups": "Rotations"}
    rtn = {
        "can_edit": not most_recent.read_only,
        "deadlines": request.app["config"]["deadlines"],
        "display_projects_link": can_view_group(request, most_recent),
        "user": user,
        "show_login_bar": isinstance(request.app["auth"], DummyAuthenticator),
        "root_title": ", ".join(root_map[perm] for perm in sorted(permissions) if perm in root_map) or
                      ("Assigned Projects" if "review_other_projects" in permissions else "Main Page"),
        "show_mark_projects": {"create_projects", "review_other_projects"} & permissions
    }
    if "view_all_submitted_projects" in permissions:
        series_groups = get_series(session, most_recent.series)
        rtn["series_years"] = sorted({group.series for group in get_all_groups(session)}, reverse=True)
        rtn["rotations"] = sorted((group.part for group in series_groups), reverse=True)
    rtn["show_submit"] = False
    if "join_projects" in permissions:
        project = get_student_project_group(session, user.id, most_recent)
        if project and project.group.student_uploadable and not project.grace_passed:
            rtn["show_submit"] = True
    if "create_project_groups" in permissions:
        rtn["groups"] = [get_dates_from_group(group) for group in series_groups]
        if most_recent.student_choice < date.today():
            rtn["show_create_rotation"] = True
    if "set_readonly" in permissions:
        rtn["show_finalise_choices"] = most_recent.can_finalise
    rtn["permissions"] = permissions
    return rtn
