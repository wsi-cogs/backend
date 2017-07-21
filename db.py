from sqlalchemy import create_engine, MetaData, Integer, String, Column, Date, ForeignKey, Boolean, Interval
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base


def base_repr(self):
    """
    Monkeypatch the Base object so it has a `eval`able
    :param self:
    :return str:
    """
    params = ", ".join("{}={}".format(k, repr(v)) for k, v in self.__dict__.items() if not k.startswith("_"))
    return f"{self.__class__.__name__}({params})"


Base = declarative_base()
Base.__repr__ = base_repr


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    projects = relationship("Project")


class ProjectGroup(Base):
    __tablename__ = "project_group"
    id = Column(Integer, primary_key=True)
    deadline_project_creation = Column(Date)
    deadline_project_approval = Column(Date)
    deadline_project_decision = Column(Date)
    deadline_project_completion = Column(Date)
    deadline_reminder_time = Column(Interval)
    series = Column(Integer)
    part = Column(Integer)
    is_readonly = Column(Boolean)

    projects = relationship("Project")


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    abstract = Column(String)
    supervisor = Column(Integer, ForeignKey(User.id))
    group = Column(Integer, ForeignKey(ProjectGroup.id))
    is_computational = Column(Boolean)
    is_wetlab = Column(Boolean)


async def init_pg(app):
    """
    Initialise the database and connect it to the app
    Also adds debugging structures to the database
    :param app:
    :return session:
    """
    conf = app["db_config"]
    engine = create_engine(f"postgresql://{conf['user']}@{conf['host']}/{conf['name']}", echo=True)
    Base.metadata.create_all(engine)
    app["db"] = engine

    Session = sessionmaker(bind=engine)
    app["session"] = session = Session()
    MetaData().create_all(engine)

    # TODO: Remove
    test_user = User(name="A supervisor")
    session.add(test_user)
    for username in ["Alpha", "Beta", "Gamma", "Zeta"]:
        session.add(User(name=username))
    test_group = ProjectGroup(series=2017,
                              part=1,
                              is_readonly=False)
    session.add(test_group)
    session.flush()
    session.add(Project(title="Studying the effects of using Lorem Ipsum text",
                        abstract="",
                        supervisor=test_user.id,
                        group=test_group.id,
                        is_computational=False,
                        is_wetlab=True))
    session.add(Project(title="Doing things with another thing",
                        abstract="Stuff happened",
                        supervisor=test_user.id,
                        group=test_group.id,
                        is_computational=True,
                        is_wetlab=True))
    session.add(Project(title="Improving performance with thing",
                        abstract="It's fun",
                        supervisor=test_user.id,
                        group=test_group.id,
                        is_computational=True,
                        is_wetlab=False))
    session.flush()
    return session


async def close_pg(app):
    """
    Clean up the database at shutdown.

    :param app:
    :return:
    """
    app["session"].close()
