from datetime import datetime

from aiohttp.web import Application
from sqlalchemy import create_engine, Integer, String, Column, Date, ForeignKey, Boolean
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from type_hints import Session


def base_repr(self):
    """
    Monkeypatch the Base object so it's `eval`able

    :param self:
    :return str:
    """
    params = ", ".join("{}={}".format(column.key, repr(getattr(self, column.key)))
                       for column in self.__table__.columns)
    return f"{self.__class__.__name__}({params})"


Base = declarative_base()
Base.__repr__ = base_repr


class ProjectGroup(Base):
    __tablename__ = "project_group"
    id = Column(Integer, primary_key=True)
    supervisor_submit = Column(Date)
    student_invite = Column(Date)
    student_choice = Column(Date)
    student_complete = Column(Date)
    marking_complete = Column(Date)
    series = Column(Integer)
    part = Column(Integer)
    student_viewable = Column(Boolean)
    student_choosable = Column(Boolean)
    student_uploadable = Column(Boolean)
    can_finalise = Column(Boolean)
    # Can supervisors modify the projects in this group
    read_only = Column(Boolean)

    projects = relationship("Project")


class ProjectGrade(Base):
    __tablename__ = "project_grade"
    id = Column(Integer, primary_key=True)
    grade_id = Column(Integer)
    good_feedback = Column(String)
    bad_feedback = Column(String)
    general_feedback = Column(String)


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    small_info = Column(String)
    abstract = Column(String)
    is_computational = Column(Boolean)
    is_wetlab = Column(Boolean)
    programmes = Column(String)

    uploaded = Column(Boolean)
    grace_passed = Column(Boolean)

    supervisor_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    cogs_marker_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    group_id = Column(Integer, ForeignKey(ProjectGroup.id, ondelete="CASCADE"))

    supervisor_feedback_id = Column(Integer, ForeignKey(ProjectGrade.id, ondelete="CASCADE"))
    cogs_feedback_id = Column(Integer, ForeignKey(ProjectGrade.id, ondelete="CASCADE"))

    supervisor = relationship("User", foreign_keys=supervisor_id, post_update=True)
    cogs_marker = relationship("User", foreign_keys=cogs_marker_id, post_update=True)
    student = relationship("User", foreign_keys=student_id, post_update=True)
    group = relationship(ProjectGroup, foreign_keys=group_id)
    supervisor_feedback = relationship(ProjectGrade, foreign_keys=supervisor_feedback_id)
    cogs_feedback = relationship(ProjectGrade, foreign_keys=cogs_feedback_id)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    user_type = Column(String)

    priority = Column(Integer)

    first_option_id = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    second_option_id = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    third_option_id = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))

    first_option = relationship(Project, foreign_keys=first_option_id, post_update=True)
    second_option = relationship(Project, foreign_keys=second_option_id, post_update=True)
    third_option = relationship(Project, foreign_keys=third_option_id, post_update=True)


class EmailTemplate(Base):
    __tablename__ = "email_template"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    subject = Column(String)
    content = Column(String)


async def init_pg(app: Application) -> Session:
    """
    Initialise the database and connect it to the app
    Also adds debugging structures to the database
    :param app:
    :return session:
    """
    conf = app["db_config"]
    engine = create_engine(f"postgresql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['name']}")
    # TODO: DELETEME
    for table in Base.metadata.tables.values():
        try:
            engine.execute(f"DROP TABLE {table} CASCADE;")
        except ProgrammingError:
            try:
                engine.execute(f'DROP TABLE "{table}" CASCADE;')
            except ProgrammingError:
                pass

    Base.metadata.create_all(engine)
    app["db"] = engine

    Session = sessionmaker(bind=engine)
    app["session"] = session = Session()

    for template in app["misc_config"]["email_whitelist"]:
        if db_helper.get_template_name(session, template) is None:
            session.add(EmailTemplate(name=template,
                                      subject=f"Subject for {template}",
                                      content=f"Content for {template}"))

    # TODO: DELETEME
    test_user = User(name="Simon Beal", email="sb48@sanger.ac.uk", user_type="supervisor|student|grad_office", priority=10)
    session.add(test_user)
    test_group_1 = ProjectGroup(series=2017,
                                part=1,
                                supervisor_submit=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_invite=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_choice=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_complete=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                marking_complete=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_viewable=True,
                                student_choosable=True,
                                student_uploadable=False,
                                can_finalise=False,
                                read_only=True)
    session.add(test_group_1)
    session.flush()
    return session


async def close_pg(app: Application) -> None:
    """
    Clean up the database at shutdown.

    :param app:
    :return:
    """
    app["session"].close()

import db_helper