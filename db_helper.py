from sqlalchemy import desc

from db import ProjectGroup, Project, User
from permissions import is_user


def get_most_recent_group(session):
    """
    Get the ProjectGroup created most recently

    :param session:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup).order_by(desc(ProjectGroup.id)).first()


def get_group(session, series: int, part: int):
    """
    Get the ProjectGroup with the corresponding series and part.

    :param session:
    :param series:
    :param part:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).filter(ProjectGroup.part == part).first()


def get_series(session, series):
    """
    Get all ProjectGroups associated the corresponding series.

    :param session:
    :param series:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).order_by(ProjectGroup.part).all()


def get_projects_user(request, user_id):
    """
    Get all the projects that belong to a user.

    :param request:
    :param user_id:
    :return:
    """
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
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def get_project_name(session, project_name):
    return session.query(Project).filter_by(title=project_name).order_by(Project.id.desc()).first()


def get_project_id(session, project_id):
    return session.query(Project).filter_by(id=project_id).first()


def get_user_cookies(cookies):
    return int(cookies.get("user_id", "-1"))


def get_user_id(session, cookies):
    return session.query(User).filter_by(id=get_user_cookies(cookies)).first()


def get_student_projects(session, cookies):
    user_id = get_user_cookies(cookies)
    return session.query(Project).filter_by(student_id=user_id).all()
