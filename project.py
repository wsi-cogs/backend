from sqlalchemy import desc
from permissions import is_user_id
from db import ProjectGroup, Project


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
    session = request.app["session"]
    cookies = request.cookies
    projects = session.query(Project).filter_by(supervisor=user_id).all()
    read_only_map = {}
    rtn = {}
    for project in projects:
        if project.group not in read_only_map:
            read_only_map[project.group] = session.query(ProjectGroup).filter_by(id=project.group).first().read_only
            rtn[project.group] = []
        project.read_only = read_only_map[project.group] or not is_user_id(cookies, project.supervisor)
        rtn[project.group].append(project)
    return (rtn[key] for key in sorted(rtn.keys(), reverse=True))
