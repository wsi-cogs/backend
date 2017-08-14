from datetime import datetime

from sqlalchemy import create_engine, Integer, String, Column, Date, ForeignKey, Boolean
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


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
    grad_office_review = Column(Date)
    student_invite = Column(Date)
    student_choice = Column(Date)
    student_complete = Column(Date)
    marking_complete = Column(Date)
    series = Column(Integer)
    part = Column(Integer)
    student_choosable = Column(Boolean)
    student_viewable = Column(Boolean)
    read_only = Column(Boolean)

    projects = relationship("Project")


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    small_info = Column(String)
    abstract = Column(String)
    supervisor_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    cogs_marker_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    group_id = Column(Integer, ForeignKey(ProjectGroup.id, ondelete="CASCADE"))
    is_computational = Column(Boolean)
    is_wetlab = Column(Boolean)

    supervisor = relationship("User", foreign_keys=supervisor_id, post_update=True)
    cogs_marker = relationship("User", foreign_keys=cogs_marker_id, post_update=True)
    student = relationship("User", foreign_keys=student_id, post_update=True)
    group = relationship(ProjectGroup, foreign_keys=group_id)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_type = Column(String)

    first_option_id = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    second_option_id = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    third_option_id = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))

    first_option = relationship(Project, foreign_keys=first_option_id, post_update=True)
    second_option = relationship(Project, foreign_keys=second_option_id, post_update=True)
    third_option = relationship(Project, foreign_keys=third_option_id, post_update=True)


async def init_pg(app):
    """
    Initialise the database and connect it to the app
    Also adds debugging structures to the database
    :param app:
    :return session:
    """
    conf = app["db_config"]
    engine = create_engine(f"postgresql://{conf['user']}@{conf['host']}/{conf['name']}")
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

    # TODO: DELETEME
    test_user = User(name="A supervisor", user_type="supervisor")
    session.add(test_user)
    test_user_2 = User(name="A student", user_type="student")
    session.add(test_user_2)
    for name in ("CoGS A", "CoGS B", "CoGS C", "CoGS D"):
        session.add(User(name=name, user_type="cogs_user"))
    test_group = ProjectGroup(series=2017,
                              part=3,
                              supervisor_submit=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                              grad_office_review=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                              student_invite=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                              student_choice=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                              student_complete=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                              marking_complete=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                              student_viewable=True,
                              student_choosable=True,
                              read_only=False)
    test_group_2 = ProjectGroup(series=2017,
                                part=1,
                                supervisor_submit=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                grad_office_review=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_invite=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_choice=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_complete=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                marking_complete=datetime.strptime("01/01/2017", "%d/%m/%Y"),
                                student_viewable=True,
                                student_choosable=True,
                                read_only=True)
    session.add(test_group_2)
    session.add(test_group)
    session.flush()
    projects = []
    projects.append(Project(title="Studying the effects of using Lorem Ipsum text",
                            small_info="Bob",
                            abstract="Pulvinar nulla vel proin elit magnis, arcu nisl per augue sem lacinia velit, accumsan cum venenatis fermentum et. Etiam fames hymenaeos penatibus, pharetra maecenas ipsum dictum.",
                            supervisor_id=test_user.id,
                            student_id=test_user.id,
                            group_id=test_group_2.id,
                            is_computational=False,
                            is_wetlab=True))
    projects.append(Project(title="Doing things with another thing",
                            small_info="Alice",
                            abstract="Stuff happened",
                            supervisor_id=test_user.id,
                            student_id=test_user.id,
                            group_id=test_group.id,
                            is_computational=False,
                            is_wetlab=True))
    projects.append(Project(title="Improving performance with thing",
                            small_info="Steve",
                            abstract="It's fun",
                            supervisor_id=test_user.id,
                            student_id=test_user.id,
                            group_id=test_group.id,
                            is_computational=True,
                            is_wetlab=False))
    projects.append(Project(title="Improving performance with thing 2",
                            small_info="Anne",
                            abstract="It's better",
                            supervisor_id=test_user.id,
                            student_id=test_user_2.id,
                            group_id=test_group.id,
                            is_computational=True,
                            is_wetlab=False))
    projects.append(Project(title="Improving performance with thing 3",
                            small_info="Pericles",
                            abstract="Stuff",
                            supervisor_id=test_user.id,
                            group_id=test_group.id,
                            is_computational=True,
                            is_wetlab=False))
    projects.append(Project(title="Improving performance with thing 4",
                            small_info="Pericles",
                            abstract="More",
                            supervisor_id=test_user.id,
                            group_id=test_group.id,
                            is_computational=True,
                            is_wetlab=False))
    for project in projects:
        session.add(project)
    test_user.first_option = projects[4]
    test_user.second_option = projects[2]
    test_user.third_option = projects[3]
    test_user_2.first_option = projects[4]
    test_user_2.second_option = projects[1]
    test_user_2.third_option = projects[2]
    session.flush()
    return session


async def close_pg(app):
    """
    Clean up the database at shutdown.

    :param app:
    :return:
    """
    app["session"].close()
