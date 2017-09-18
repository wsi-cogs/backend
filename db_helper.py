from collections import defaultdict
from datetime import date
from typing import Optional, List, Union, Dict

from aiohttp.web import Application
from sqlalchemy import desc

from db import ProjectGroup, Project, User, EmailTemplate
from permissions import is_user
from type_hints import Session, Cookies


def get_most_recent_group(session: Session) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup created most recently

    :param session:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup).order_by(desc(ProjectGroup.id)).first()


def get_group(session: Session, series: int, part: int) -> Optional[ProjectGroup]:
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


def get_series(session: Session, series: int) -> List[ProjectGroup]:
    """
    Get all ProjectGroups associated the corresponding series.

    :param session:
    :param series:
    :return ProjectGroup:
    """
    assert isinstance(series, int)
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).order_by(ProjectGroup.part).all()


def get_projects_supervisor(session: Session, user_id: int) -> List[List[Project]]:
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


def get_projects_cogs(session: Session, cookies: Cookies) -> List[List[Project]]:
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


def set_project_read_only(cookies: Cookies, project: Project):
    project.read_only = project.group.read_only or not is_user(cookies, project.supervisor)


def set_project_can_resubmit(session: Session, cookies: Cookies, project: Project):
    most_recent = get_most_recent_group(session)
    if project.group == most_recent:
        project.can_resubmit = False
    else:
        project.can_resubmit = project.group.read_only and is_user(cookies, project.supervisor)


def set_project_can_mark(cookies: Cookies, project: Project):
    project.can_mark = can_provide_feedback(cookies, project)


def get_project_name(session: Session, project_name: str) -> Optional[Project]:
    """
    Get a project by it's name.
    If there is already a project with this name, return the newest one.

    :param session:
    :param project_name:
    :return:
    """
    assert isinstance(project_name, str)
    return session.query(Project).filter_by(title=project_name).order_by(Project.id.desc()).first()


def get_project_id(session: Session, project_id: int) -> Optional[Project]:
    """
    Get a project by it's id.

    :param session:
    :param project_id:
    :return:
    """
    assert isinstance(project_id, int)
    return session.query(Project).filter_by(id=project_id).first()


def get_user_cookies(cookies: Cookies) -> int:
    """
    Get the user id of the current logged in user or -1

    :param cookies:
    :return:
    """
    return int(cookies.get("user_id", "-1"))


def get_user_id(session: Session, cookies: Optional[Cookies]=None, user_id: Optional[int]=None) -> Optional[User]:
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


def get_all_users(session: Session) -> List[User]:
    """
    Get all users in the system

    :param session:
    :return:
    """
    return session.query(User).all()


def get_all_groups(session: Session) -> List[ProjectGroup]:
    """
    Get all rotations in the system

    :param session:
    :return:
    """
    return session.query(ProjectGroup).all()


def get_student_projects(session: Session, cookies: Cookies) -> List[Project]:
    """
    Returns a list of projects the current logged in user is a student for

    :param session:
    :param cookies:
    :return:
    """
    user_id = get_user_cookies(cookies)
    projects = session.query(Project).filter_by(student_id=user_id).all()
    return sort_by_attr(projects, "id")


def get_student_project_group(session: Session, user_id: int, group: ProjectGroup):
    """


    :param session:
    :param user_id:
    :param group:
    :return:
    """
    assert isinstance(user_id, int)
    project = session.query(Project).filter_by(student_id=user_id).filter_by(group_id=group.id).first()
    return project


def get_students_series(session: Session, series: int):
    assert isinstance(series, int)
    rotations = get_series(session, series)
    students = []
    for rotation in rotations:
        for project in rotation.projects:
            if project.student not in students:
                students.append(project.student)
    return students


def can_provide_feedback(cookies: Cookies, project: Project) -> bool:
    """
    Can a user provide feedback to a project?

    :param cookies:
    :param project:
    :return:
    """
    logged_in_user = get_user_cookies(cookies)
    if project.grace_passed:
        return should_pester_feedback(project, user_id=logged_in_user)
    return False


def should_pester_upload(app: Application, user: User) -> bool:
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


def should_pester_feedback(project: Project, user_id: int) -> bool:
    """
    Should the system pester a user to provide feedback on a project?
    It should if they haven't yet done so.

    :param project:
    :param user_id:
    :return:
    """
    if user_id == project.supervisor.id:
        return project.supervisor_feedback_id is None
    elif user_id == project.cogs_marker.id:
        return project.cogs_feedback_id is None
    return False


def set_group_attributes(session: Session, cookies: Cookies, group: Union[ProjectGroup, List[Project]]) -> List[Project]:
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
        set_project_can_resubmit(session, cookies, project)
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


def get_dates_from_group(group: ProjectGroup) -> Dict:
    rtn = {}
    for column in group.__table__.columns:
        rtn[column.key] = getattr(group, column.key)
        if isinstance(rtn[column.key], date):
            rtn[column.key] = rtn[column.key].strftime("%d/%m/%Y")
    return rtn


def get_templates(session: Session) -> List[EmailTemplate]:
    """
    Get all EmailTemplate associated the corresponding series.

    :param session:
    :return List[EmailTemplate]:
    """
    return session.query(EmailTemplate).order_by(EmailTemplate.name).all()


def get_template_name(session: Session, name: str) -> EmailTemplate:
    """
    Get all EmailTemplate associated the corresponding series.

    :param session:
    :param name:
    :return EmailTemplate:
    """
    return session.query(EmailTemplate).filter_by(name=name).first()
