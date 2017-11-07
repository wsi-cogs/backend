"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
* Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from cogs.common.types import Application, DBSession


async def start(app:Application) -> DBSession:
    """
    Initialise the database and thread it through the application
    Also adds debugging structures to the database

    :param app:
    :return session:
    """
    import db_helper

    conf = app["config"]["db"]
    engine = create_engine(f"postgresql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['name']}")

    if "reset_db" in sys.argv:
        print("Resetting database...")
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

    for template in app["config"]["misc"]["email_whitelist"]:
        if db_helper.get_template_name(session, template) is None:
            session.add(EmailTemplate(name=template,
                                      subject=f"Subject for {template}",
                                      content=f"Content for {template}"))

    if not db_helper.get_all_users(session):
        print("No users found. Adding admins. (sb48 & ca3)")
        session.add(User(name="Simon Beal", email="sb48@sanger.ac.uk", user_type="grad_office", priority=0))
        session.add(User(name="Carl Anderson", email="ca3@sanger.ac.uk", user_type="grad_office", priority=0))
    if not db_helper.get_all_groups(session):
        print("No groups found. Adding rotation 1 2017.")
        session.add(ProjectGroup(series=2017,
                                 part=1,
                                 supervisor_submit=datetime.strptime("18/07/2017", "%d/%m/%Y"),
                                 student_invite=datetime.strptime("08/08/2017", "%d/%m/%Y"),
                                 student_choice=datetime.strptime("30/08/2017", "%d/%m/%Y"),
                                 student_complete=datetime.strptime("20/12/2017", "%d/%m/%Y"),
                                 marking_complete=datetime.strptime("15/01/2018", "%d/%m/%Y"),
                                 student_viewable=True,
                                 student_choosable=True,
                                 student_uploadable=False,
                                 can_finalise=True,
                                 read_only=False))

    session.commit()
    return session


async def stop(app:Application) -> None:
    """
    Clean up the database at shutdown

    :param app:
    :return:
    """
    app["session"].close()
