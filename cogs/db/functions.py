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
from cogs.common.types import Application, DBSession, Cookies
from cogs.permissions import is_user, get_user_permissions, can_view_group
from .models import ProjectGroup, Project, User, EmailTemplate


def get_most_recent_group(session:DBSession) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup created most recently

    :param session:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup) \
                  .order_by(desc(ProjectGroup.id)) \
                  .first()


def get_group(session:DBSession, series:int, part:int) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup with the corresponding series and part

    :param session:
    :param series:
    :param part:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup) \
                  .filter(ProjectGroup.series == series) \
                  .filter(ProjectGroup.part == part) \
                  .first()


def get_series(session:DBSession, series:int) -> List[ProjectGroup]:
    """
    Get all ProjectGroups associated the corresponding series

    :param session:
    :param series:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup) \
                  .filter(ProjectGroup.series == series) \
                  .order_by(ProjectGroup.part) \
                  .all()


def get_projects_supervisor(session:DBSession, user_id:int) -> List[List[Project]]:
    """
    Get all the projects that belong to a user

    :param session:
    :param user_id:
    :return:
    """
    # TODO Tidy up
    # FIXME What the hell is going on here? What's the point of
    # read_only_map? Why do I want a list of lists returned?...
    projects = session.query(Project).filter_by(supervisor_id=user_id).all()
    read_only_map = {}
    rtn = {}
    for project in projects:
        if project.group_id not in read_only_map:
            read_only_map[project.group_id] = project.group.read_only
            rtn[project.group_id] = []
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def get_projects_cogs(app:Application, cookies:Cookies) -> List[List[Project]]:
    """
    Get a list of projects for which the logged in user is the CoGS marker

    :param app:
    :param cookies:
    :return:
    """
    # TODO Tidy up
    user_id = get_user_cookies(app, cookies)
    projects = app["session"].query(Project).filter_by(cogs_marker_id=user_id).all()
    rtn = defaultdict(list)
    for project in projects:
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def set_project_read_only(app:Application, cookies:Cookies, project:Project) -> None:
    """
    TODO: Docstring
    """
    project.read_only = project.group.read_only \
                        or not is_user(app, cookies, project.supervisor)


def set_project_can_resubmit(app:Application, cookies:Cookies, project:Project) -> None:
    """
    TODO: Docstring
    """
    most_recent = get_most_recent_group(app["session"])

    project.can_resubmit = project.group == most_recent \
                       and project.group.read_only \
                       and is_user(app, cookies, project.supervisor)


def set_project_can_mark(app:Application, cookies:Cookies, project:Project) -> None:
    """
    TODO: Docstring
    """
    project.can_mark = can_provide_feedback(app, cookies, project)


def get_project_name(session:DBSession, project_name:str) -> Optional[Project]:
    """
    Get the newest project by its name, if it exists

    :param session:
    :param project_name:
    :return:
    """
    return session.query(Project) \
                  .filter_by(title=project_name) \
                  .order_by(Project.id.desc()) \
                  .first()


def get_project_id(session:DBSession, project_id:int) -> Optional[Project]:
    """
    Get a project by its ID

    :param session:
    :param project_id:
    :return:
    """
    return session.query(Project) \
                  .filter_by(id=project_id) \
                  .first()


def get_user_cookies(app:Application, cookies:Cookies) -> int:
    """
    Get the user ID of the current logged in user

    :param app:
    :param cookies:
    :return:
    """
    auth = app["auth"]
    if isinstance(auth, DummyAuthenticator):
        # Always return the root user if there's no authentication
        return 1

    try:
        email = auth.extract_email_from_source(cookies)
    except AuthenticationError:
        # TODO? Keep the exception; we now have a much richer signalling
        # system to deduce what went wrong during authentication
        return -1

    user = app["session"].query(User) \
                         .filter_by(email=email) \
                         .first()

    if not user:
        # TODO? Again, better to raise an exception here
        return -1

    return user.id


def get_user_id(app:Application, cookies:Optional[Cookies] = None, user_id:Optional[int] = None) -> Optional[User]:
    """
    Get a user, either by the currently logged in one or by user ID

    :param app:
    :param cookies:
    :param user_id:
    :return:
    """
    assert cookies or user_id, "Must provide either cookies or user_id"

    if not cookies:
        user_id = get_user_cookies(app, cookies)

    return app["session"].query(User).filter_by(id=user_id).first()


def get_all_users(session:DBSession) -> List[User]:
    """
    Get all users in the system

    :param session:
    :return:
    """
    return session.query(User).all()


def get_all_groups(session:DBSession) -> List[ProjectGroup]:
    """
    Get all rotations in the system

    :param session:
    :return:
    """
    return session.query(ProjectGroup).all()


def get_student_projects(app:Application, cookies:Cookies) -> List[Project]:
    """
    Returns a list of projects for which the currently logged in user is
    a student

    :param app:
    :param cookies:
    :return:
    """
    user_id = get_user_cookies(app, cookies)
    projects = app["session"].query(Project).filter_by(student_id=user_id).all()
    return sort_by_attr(projects, "id")


def get_student_project_group(session:DBSession, user_id:int, group:ProjectGroup) -> Project:
    """
    TODO: Docstring

    :param session:
    :param user_id:
    :param group:
    :return:
    """
    return session.query(Project) \
                  .filter_by(student_id=user_id) \
                  .filter_by(group_id=group.id) \
                  .first()


def get_students_series(session:DBSession, series:int) -> List:
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


def can_provide_feedback(app:Application, cookies:Cookies, project:Project) -> bool:
    """
    Can a user provide feedback to a project?

    :param app:
    :param cookies:
    :param project:
    :return:
    """
    # TODO Tidy up
    logged_in_user = get_user_cookies(app, cookies)
    if project.grace_passed:
        return should_pester_feedback(project, user_id=logged_in_user)
    return False


def should_pester_upload(app:Application, user:User) -> bool:
    """
    Should the system pester a supervisor to upload projects?
    It should if they haven't uploaded one for this group.

    :param app:
    :param user:
    :return:
    """
    # TODO Tidy up
    group = get_most_recent_group(app["session"])
    for project in group.projects:
        if project.supervisor == user:
            return False
    return True


def should_pester_feedback(project:Project, user_id:int) -> bool:
    """
    Should the system pester a user to provide feedback on a project?
    It should if they haven't yet done so.

    :param project:
    :param user_id:
    :return:
    """
    # TODO Tidy up
    if user_id == project.supervisor.id:
        return project.supervisor_feedback_id is None
    elif user_id == project.cogs_marker.id:
        return project.cogs_feedback_id is None
    return False


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


def get_templates(session:DBSession) -> List[EmailTemplate]:
    """
    Get all EmailTemplate associated the corresponding series

    :param session:
    :return List[EmailTemplate]:
    """
    return session.query(EmailTemplate) \
                  .order_by(EmailTemplate.name) \
                  .all()


def get_template_name(session:DBSession, name:str) -> EmailTemplate:
    """
    Get all EmailTemplate associated the corresponding series

    :param session:
    :param name:
    :return EmailTemplate:
    """
    return session.query(EmailTemplate) \
                  .filter_by(name=name) \
                  .first()


def rgetattr(obj:Any, attr:str, default:str = "") -> Any:
    # FIXME I dunno what this is all about :P
    return reduce(lambda inner_obj, inner_attr: getattr(inner_obj, inner_attr, default), [obj] + attr.split('.'))
