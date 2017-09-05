from collections import defaultdict
from typing import Optional, List, Union

from sqlalchemy import desc

from db import ProjectGroup, Project, User
from permissions import is_user


def get_most_recent_group(session) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup created most recently

    :param session:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup).order_by(desc(ProjectGroup.id)).first()


def get_group(session, series: int, part: int) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup with the corresponding series and part.

    :param session:
    :param series:
    :param part:
    :return ProjectGroup:
    """
    assert isinstance(series, int)
    assert isinstance(part, int)
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).filter(ProjectGroup.part == part).first()


def get_series(session, series: int) -> List[ProjectGroup]:
    """
    Get all ProjectGroups associated the corresponding series.

    :param session:
    :param series:
    :return ProjectGroup:
    """
    assert isinstance(series, int)
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).order_by(ProjectGroup.part).all()


def get_projects_supervisor(session, user_id: int) -> List[List[Project]]:
    """
    Get all the projects that belong to a user.

    :param session:
    :param user_id:
    :return:
    """
    assert isinstance(user_id, int)
    projects = session.query(Project).filter_by(supervisor_id=user_id).all()
    read_only_map = {}
    rtn = {}
    for project in projects:
        if project.group_id not in read_only_map:
            read_only_map[project.group_id] = project.group.read_only
            rtn[project.group_id] = []
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def get_projects_cogs(session, cookies) -> List[List[Project]]:
    """
    Get a list of projects the logged in user is the CoGS marker for

    :param session:
    :param cookies:
    :return:
    """
    user_id = get_user_cookies(cookies)
    projects = session.query(Project).filter_by(cogs_marker_id=user_id).all()
    rtn = defaultdict(list)
    for project in projects:
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def set_project_read_only(cookies, project: Project):
    project.read_only = project.group.read_only or not is_user(cookies, project.supervisor)


def set_project_can_resubmit(cookies, project: Project):
    project.can_resubmit = project.group.read_only and is_user(cookies, project.supervisor)


def set_project_can_mark(cookies, project: Project):
    project.can_mark = can_provide_feedback(cookies, project)


def get_project_name(session, project_name: str) -> Optional[Project]:
    """
    Get a project by it's name.
    If there is already a project with this name, return the newest one.

    :param session:
    :param project_name:
    :return:
    """
    assert isinstance(project_name, str)
    return session.query(Project).filter_by(title=project_name).order_by(Project.id.desc()).first()


def get_project_id(session, project_id: int) -> Optional[Project]:
    """
    Get a project by it's id.

    :param session:
    :param project_id:
    :return:
    """
    assert isinstance(project_id, int)
    return session.query(Project).filter_by(id=project_id).first()


def get_user_cookies(cookies) -> int:
    """
    Get the user id of the current logged in user or -1

    :param cookies:
    :return:
    """
    return int(cookies.get("user_id", "-1"))


def get_user_id(session, cookies=None, user_id: Optional[int]=None) -> Optional[User]:
    """
    Get a user, either by the current logged in one or by user id

    :param session:
    :param cookies:
    :param user_id:
    :return:
    """
    assert not (cookies is None and user_id is None), "Must pass either cookies or user_id"
    if cookies is not None:
        user_id = get_user_cookies(cookies)
    assert isinstance(user_id, int)
    return session.query(User).filter_by(id=user_id).first()


def get_all_users(session) -> List[User]:
    """
    Get all users in the system

    :param session:
    :return:
    """
    return session.query(User).all()


def get_all_groups(session) -> List[ProjectGroup]:
    """
    Get all rotations in the system

    :param session:
    :return:
    """
    return session.query(ProjectGroup).all()


def get_student_projects(session, cookies) -> List[Project]:
    """
    Returns a list of projects the current logged in user is a student for

    :param session:
    :param cookies:
    :return:
    """
    user_id = get_user_cookies(cookies)
    projects = session.query(Project).filter_by(student_id=user_id).all()
    return sort_by_attr(projects, "id")


def can_provide_feedback(cookies, project: Project) -> bool:
    """
    Can a user provide feedback to a project?

    :param cookies:
    :param project:
    :return:
    """
    logged_in_user = get_user_cookies(cookies)
    if not project.grace_passed:
        return should_pester_feedback(project, user=logged_in_user)
    return False


def should_pester_upload(app, user: User) -> bool:
    """
    Should the system pester a supervisor to upload projects?
    It should if they haven't uploaded one for this group.

    :param app:
    :param user:
    :return:
    """
    group = get_most_recent_group(app["session"])
    for project in group.projects:
        if project.supervisor == user:
            return False
    return True


def should_pester_feedback(project: Project, user: User) -> bool:
    """
    Should the system pester a user to provide feedback on a project?
    It should if they haven't yet done so.

    :param project:
    :param user:
    :return:
    """
    if user == project.supervisor:
        return project.supervisor_feedback_id is None
    elif user == project.cogs_marker:
        return project.cogs_feedback_id is None
    return False


def set_group_attributes(cookies, group: Union[ProjectGroup, List[Project]]) -> List[Project]:
    """
    Return a list of all the projects in a ProjectGroup

    :param cookies:
    :param group:
    :return:
    """
    try:
        projects = group.projects
    except AttributeError:
        projects = group
    for project in projects:
        set_project_can_mark(cookies, project)
        set_project_can_resubmit(cookies, project)
        set_project_read_only(cookies, project)
    return sort_by_attr(projects, "can_mark")


def sort_by_attr(projects: List[Project], attr: str) -> List[Project]:
    """
    Sort a list of projects by an attribute of a project.

    :param projects:
    :param attr:
    :return:
    """
    projects.sort(key=lambda project: getattr(project, attr), reverse=True)
    return projects

