from sqlalchemy import desc
from db import ProjectGroup


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
