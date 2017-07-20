from sqlalchemy import desc
from db import ProjectGroup


def get_most_recent_group(session):
    return session.query(ProjectGroup).order_by(desc(ProjectGroup.id)).first()


def get_group(series, part, session):
    return session.query(ProjectGroup).filter(ProjectGroup.series==series).filter(ProjectGroup.part==part).first()
