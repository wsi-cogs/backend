from collections import defaultdict
from typing import Optional, List

from sqlalchemy import desc

from db import ProjectGroup, Project, User
from permissions import is_user, can_choose_project


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


def get_projects_supervisor(request, user_id: int) -> List[List[Project]]:
    """
    Get all the projects that belong to a user.

    :param request:
    :param user_id:
    :return:
    """
    assert isinstance(user_id, int)
    session = request.app["session"]
    cookies = request.cookies
    projects = session.query(Project).filter_by(supervisor_id=user_id).all()
    read_only_map = {}
    rtn = {}
    for project in projects:
        if project.group_id not in read_only_map:
            read_only_map[project.group_id] = project.group.read_only
            rtn[project.group_id] = []
        project.read_only = read_only_map[project.group_id] or not is_user(cookies, project.supervisor)
        project.can_resubmit = read_only_map[project.group_id] and is_user(cookies, project.supervisor)
        project.can_mark = can_provide_feedback(cookies, project)
        rtn[project.group_id].append(project)
    return [sort_by_attr(rtn[key], "can_mark") for key in sorted(rtn.keys(), reverse=True)]


def get_projects_cogs(session, cookies) -> List[List[Project]]:
    user_id = get_user_cookies(cookies)
    projects = session.query(Project).filter_by(cogs_marker_id=user_id).all()
    rtn = defaultdict(list)
    for project in projects:
        project.can_mark = can_provide_feedback(cookies, project)
        rtn[project.group_id].append(project)
    return [sort_by_attr(rtn[key], "can_mark") for key in sorted(rtn.keys(), reverse=True)]


def get_project_name(session, project_name: str) -> Optional[Project]:
    assert isinstance(project_name, str)
    return session.query(Project).filter_by(title=project_name).order_by(Project.id.desc()).first()


def get_project_id(session, project_id: int) -> Optional[Project]:
    assert isinstance(project_id, int)
    return session.query(Project).filter_by(id=project_id).first()


def get_user_cookies(cookies) -> int:
    return int(cookies.get("user_id", "-1"))


def get_user_id(session, cookies=None, user_id: Optional[int]=None) -> Optional[User]:
    if cookies is not None:
        user_id = get_user_cookies(cookies)
    assert isinstance(user_id, int)
    return session.query(User).filter_by(id=user_id).first()


def get_all_users(session) -> List[User]:
    return session.query(User).all()


def get_all_groups(session) -> List[ProjectGroup]:
    return session.query(ProjectGroup).all()


def get_student_projects(session, cookies) -> List[Project]:
    user_id = get_user_cookies(cookies)
    projects = session.query(Project).filter_by(student_id=user_id).all()
    return sort_by_attr(projects, "id")


def can_provide_feedback(cookies, project: Project) -> bool:
    logged_in_user = get_user_cookies(cookies)
    if not project.grace_passed:
        if logged_in_user == project.supervisor_id:
            return not project.supervisor_feedback_id
        if logged_in_user == project.cogs_marker_id:
            return not project.cogs_feedback_id
    return False


def get_group_projects(request, group: ProjectGroup) -> List[Project]:
    """
    Return a list of all the projects in a ProjectGroup

    :param request:
    :param group:
    :return:
    """
    session = request.app["session"]
    cookies = request.cookies
    for project in group.projects:
        project.read_only = group.read_only or not is_user(cookies, project.supervisor)
        project.show_vote = can_choose_project(session, cookies, project)
        project.can_mark = can_provide_feedback(cookies, project)
    return sort_by_attr(group.projects, "can_mark")


def sort_by_attr(projects: List[Project], attr: str) -> List[Project]:
    return sorted(projects, key=lambda project: getattr(project, attr), reverse=True)

