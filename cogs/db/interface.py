"""
Copyright (c) 2017, 2018 Genome Research Ltd.

Authors:
* Christopher Harrison <ch12@sanger.ac.uk>
* Simon Beal <sb48@sanger.ac.uk>

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

import atexit
from datetime import datetime
from typing import Dict, List, Optional, overload
from typing_extensions import Literal

from sqlalchemy import create_engine, desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from sqlalchemy.exc import ProgrammingError


from cogs.common import logging
from cogs.common.constants import PERMISSIONS
from .models import Base, EmailTemplate, Project, ProjectGroup, User
from .session import ContextLocalRegistry

class Database(logging.LogWriter):
    """Database interface."""

    _engine: Engine
    _session: Session

    def __init__(self, config: Dict) -> None:
        """Constructor: Connect to and initialise the database session."""
        # Connect to database and instantiate models
        self.log(logging.DEBUG, "Connecting to PostgreSQL database \"{name}\" at {host}:{port}".format(**config))
        self._engine = create_engine("postgresql://{user}:{passwd}@{host}:{port}/{name}".format(**config))
        Base.metadata.create_all(self._engine)

        # Start session (and register close on exit)
        session_factory = sessionmaker(bind=self._engine)
        Session = scoped_session(session_factory)
        # Set session registry (which stores a session for each context)
        Session.registry = ContextLocalRegistry(session_factory)
        self._session = Session

        atexit.register(self._session.close)

        self._create_minimal()

    def _create_minimal(self) -> None:
        """Create minimal data in the database for a working system."""
        # Set up the e-mail template placeholders for rotation
        # invitations, if they don't already exist

        # Delay this import, because cogs.mail imports cogs.db, so doing it
        # earlier results in circular imports.
        import cogs.mail.postman

        all_db_templates = [template.name for template in self.get_all_templates()]

        for name, subject, content in cogs.mail.postman.get_filesystem_templates(exclude=all_db_templates):
            self._session.add(EmailTemplate(name=name,
                                            subject=subject,
                                            content=content))

        # TODO Tidy the below up / set the defaults more appropriately

        if not self.get_all_users():
            self.log(logging.INFO, "No users found. Adding admins.")
            _admin_args = {"user_type": "grad_office", "priority": 0, "email_personal": None}
            self._session.add(User(name="Simon Beal",           email="sb48@sanger.ac.uk", **_admin_args))
            self._session.add(User(name="Carl Anderson",        email="ca3@sanger.ac.uk",  **_admin_args))
            self._session.add(User(name="Christopher Harrison", email="ch12@sanger.ac.uk", **_admin_args))
            self._session.add(User(name="Josh Holland"        , email="jh36@sanger.ac.uk", **_admin_args))

        if not self._session.query(ProjectGroup).all():
            # NB: this rotation has its state attributes set to provoke
            # special handling in the frontend -- it's important that
            # users create a new rotation and ignore this one, so the
            # frontend will refuse to modify this rotation.
            self.log(logging.INFO, "No rotations found. Adding rotation 1 2017.")
            self._session.add(ProjectGroup(series=2017,
                                           part=1,
                                           supervisor_submit=datetime.strptime("18/07/2017", "%d/%m/%Y"),
                                           student_invite=datetime.strptime("08/08/2017", "%d/%m/%Y"),
                                           student_choice=datetime.strptime("30/08/2017", "%d/%m/%Y"),
                                           student_complete=datetime.strptime("20/12/2017", "%d/%m/%Y"),
                                           marking_complete=datetime.strptime("15/01/2018", "%d/%m/%Y"),
                                           student_viewable=False,
                                           student_choosable=False,
                                           student_uploadable=False,
                                           can_finalise=False,
                                           read_only=True))
        self._session.commit()

    def reset_all(self) -> None:
        """Reset everything in the database. For debugging use only!"""
        for table in Base.metadata.tables.values():
            try:
                self.engine.execute(f"DROP TABLE {table} CASCADE;")
            except ProgrammingError:
                try:
                    self.engine.execute(f'DROP TABLE "{table}" CASCADE;')
                except ProgrammingError:
                    pass
        Base.metadata.create_all(self._engine)
        self._create_minimal()

    ## Convenience methods and properties ##############################

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def session(self) -> Session:
        return self._session

    def add(self, model: Base) -> None:
        self._session.add(model)

    def commit(self) -> None:
        self._session.commit()

    ## E-Mail Template Methods #########################################

    def get_template_by_name(self, name: str) -> Optional[EmailTemplate]:
        """Get an e-mail template by its name."""
        q = self._session.query(EmailTemplate)
        return q.filter(EmailTemplate.name == name) \
                .first()

    def get_all_templates(self) -> List[EmailTemplate]:
        """Get all e-mail templates in the system."""
        return self._session.query(EmailTemplate) \
                            .order_by(EmailTemplate.name) \
                            .all()

    ## Project Methods #################################################

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get a project by its ID."""
        q = self._session.query(Project)
        return q.filter(Project.id == project_id) \
                .first()

    @overload
    def get_projects_by_student(self, student: User, group: None = None) -> List[Project]:
        ...
    @overload
    def get_projects_by_student(self, student: User, group: ProjectGroup) -> Optional[Project]:
        ...
    def get_projects_by_student(self, student, group = None):
        """
        Get the list of projects for the specified student or, if a
        project group is specified, that student's project in that group
        """
        q = self._session.query(Project)
        attr = "all"

        clause = (Project.student == student)
        if group:
            clause &= (Project.group == group)
            attr = "first"

        return getattr(q.filter(clause) \
                        .order_by(Project.group_id), attr)()

    def get_projects_by_supervisor(self, supervisor: User, group: Optional[ProjectGroup] = None) -> List[Project]:
        """Get the list of projects owned by the specified supervisor.

        Optionally, the list can be restricted to a given rotation.
        """
        q = self._session.query(Project)

        clause = (Project.supervisor == supervisor)
        if group:
            clause &= (Project.group == group)

        return q.filter(clause) \
                .order_by(Project.id) \
                .all()

    def get_projects_by_cogs_marker(self, cogs_marker: User, group: Optional[ProjectGroup] = None) -> List[Project]:
        """Get the list of projects with the specified CoGS marker.

        Optionally, the list can be restricted to a given rotation.
        """
        q = self._session.query(Project)

        clause = (Project.cogs_marker == cogs_marker)
        if group:
            clause &= (Project.group == group)

        return q.filter(clause) \
                .order_by(Project.id) \
                .all()

    ## Project Group Methods ###########################################

    def get_project_group(self, series: int, part: int) -> Optional[ProjectGroup]:
        """Get the rotation for the specified series and part."""
        q = self._session.query(ProjectGroup)
        return q.filter(
                 (ProjectGroup.series == series) & (ProjectGroup.part == part)
               ).first()

    def get_rotation_by_id(self, id: int) -> Optional[ProjectGroup]:
        """Get the rotation with the specified ID, or None."""
        return (
            self._session.query(ProjectGroup)
            .filter(ProjectGroup.id == id)
            .one_or_none()
        )

    def get_project_groups_by_series(self, series: int) -> List[ProjectGroup]:
        """Get all rotations for the specified series."""
        q = self._session.query(ProjectGroup)
        return q.filter(ProjectGroup.series == series) \
                .order_by(ProjectGroup.part) \
                .all()

    def get_most_recent_group(self) -> Optional[ProjectGroup]:
        """Get the most recently created project group.

        NB: this assumes that the database assigns IDs sequentially!
        """
        q = self._session.query(ProjectGroup)
        return q.order_by(desc(ProjectGroup.id)) \
                .first()

    ## Series Methods ##################################################

    # FIXME "Series" broadly represents academic years (i.e., a set of
    # rotations/project groups). Currently these don't exist as a
    # database entity; they just implicitly exist by virtue of their ID
    # corresponding to the calendar year at the start of the series.
    # This comes with a lot of assumptions, that could be done away with
    # by explicitly defining series. This would have the additional
    # benefit of defining a proper object hierarchy, which is where most
    # of these methods belong (rather than in this database God-object).

    def get_students_in_series(self, series: int) -> List[User]:
        """
        Get the list of all students who are enrolled on projects in the
        given series
        """
        # TODO This would be better implemented as a join in the
        # database, rather than rolling our own.
        return list({
            project.student
            for rotation in self.get_project_groups_by_series(series)
            for project in rotation.projects
            if project.student is not None})

    def get_all_years(self) -> List[int]:
        """Get the complete, sorted list of years."""
        q = self._session.query(ProjectGroup)
        return [
            group.series
            for group in q.distinct(ProjectGroup.series) \
                          .order_by(desc(ProjectGroup.series)) \
                          .all()]

    def get_all_series(self) -> List[ProjectGroup]:
        """Get every series in the database."""
        q = self._session.query(ProjectGroup)
        return q.order_by(desc(ProjectGroup.id)) \
                .all()

    ## User Methods ####################################################

    # A few bits of code assume that user 1 will always exist.
    # If it ever becomes possible to delete users, revisit this!
    @overload
    def get_user_by_id(self, uid: Literal[1]) -> User:
        ...
    @overload
    def get_user_by_id(self, uid: int) -> Optional[User]:
        ...
    def get_user_by_id(self, uid):
        """Get a user by their ID."""
        q = self._session.query(User)
        return q.filter(User.id == uid) \
                .first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their e-mail address."""
        q = self._session.query(User)
        return q.filter((User.email == email) | (User.email_personal == email)) \
                .first()

    def get_users_by_permission(self, *permissions: str) -> List[User]:
        """Return the users who have any of the specified permissions."""
        # We must have at least one permission and our given permissions
        # must be a subset of the valid permissions
        assert permissions
        assert set(permissions) <= set(PERMISSIONS)

        return [
            user
            for user in self.get_all_users()
            if any(getattr(user.role, p) for p in permissions)]

    def get_all_users(self) -> List[User]:
        """Get all users in the system."""
        return self._session.query(User).all()
