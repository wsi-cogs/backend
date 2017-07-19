from sqlalchemy import create_engine, MetaData, Integer, String, Column, Date, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base


def base_repr(self):
    params = ", ".join("{}={}".format(k, repr(v)) for k, v in self.__dict__.items() if not k.startswith("_"))
    return f"{self.__class__.__name__}({params})"


Base = declarative_base()
Base.__repr__ = base_repr


async def init_pg(app):
    conf = app["db_config"]
    engine = create_engine(f"postgresql://{conf['user']}@{conf['host']}/{conf['name']}", echo=True)
    Base.metadata.create_all(engine)
    app["db"] = engine
    app["session"] = await setup(engine)


async def close_pg(app):
    app["session"].close()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    projects = relationship("Project")


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    abstract = Column(String)
    supervisor = Column(Integer, ForeignKey(User.id))
    is_computational = Column(Boolean)
    is_wetlab = Column(Boolean)
    is_readonly = Column(Boolean)


async def setup(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    MetaData().create_all(engine)

    test_user = User(name="test")
    session.add(test_user)
    for username in ["Alpha", "Beta", "Gamma", "Zeta"]:
        session.add(User(name=username))
    session.flush()
    session.add(Project(title="Title",
                        abstract="An abstract",
                        supervisor=test_user.id,
                        is_computational=False,
                        is_wetlab=True,
                        is_readonly=False))
    return session