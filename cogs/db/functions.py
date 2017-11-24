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

import json
from collections import defaultdict
from datetime import date
from functools import reduce
from typing import Optional, List, Union, Dict, Any

from sqlalchemy import desc

from cogs.auth.dummy import DummyAuthenticator
from cogs.auth.exceptions import AuthenticationError
from cogs.common.types import Application, Cookies
#from cogs.security import is_user, get_user_permissions, can_view_group
from .models import ProjectGroup, Project, User, EmailTemplate
















def get_students_series(session, series:int) -> List:
    """
    TODO: Docstring
    """
    # TODO Tidy up
    rotations = get_series(session, series)
    students = []
    for rotation in rotations:
        for project in rotation.projects:
            if project.student not in students:
                students.append(project.student)
    return students



def set_group_attributes(app, cookies:Cookies, group:Union[ProjectGroup, List[Project]]) -> List[Project]:
    """
    Return a list of all the projects in a ProjectGroup

    :param app:
    :param cookies:
    :param group:
    :return:
    """
    # TODO Tidy up
    try:
        projects = group.projects
    except AttributeError:
        projects = group

    for project in projects:
        set_project_can_mark(app, cookies, project)
        set_project_can_resubmit(app, cookies, project)
        set_project_read_only(app, cookies, project)
    sort_by_attr(projects, "supervisor.name")
    return sort_by_attr(projects, "can_mark")


def sort_by_attr(projects:List[Project], attr:str) -> List[Project]:
    """
    Sort a list of projects by an attribute of a project

    :param projects:
    :param attr:
    :return:
    """
    # FIXME Do we need to sort the reference *and* return; would
    # return sorted(projects, ...) be better?
    projects.sort(key=lambda project: rgetattr(project, attr), reverse=True)
    return projects


def get_dates_from_group(group:ProjectGroup) -> Dict:
    """
    TODO: Docstring
    """
    # TODO Tidy up
    rtn = {}
    for column in group.__table__.columns:
        rtn[column.key] = getattr(group, column.key)
        if isinstance(rtn[column.key], date):
            rtn[column.key] = rtn[column.key].strftime("%d/%m/%Y")
    return rtn


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


def rgetattr(obj:Any, attr:str, default:str = "") -> Any:
    # FIXME I dunno what this is all about :P
    return reduce(lambda inner_obj, inner_attr: getattr(inner_obj, inner_attr, default), [obj] + attr.split('.'))
