"""
Copyright (c) 2017 Genome Research Ltd.

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

from sqlalchemy import create_engine, desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from cogs.common import logging
from cogs.common.constants import ROTATION_TEMPLATE_IDS
from .models import Base, EmailTemplate, Project, ProjectGroup, User


class Database(logging.LogWriter):
    """ Database interface """
    _engine:Engine
    _session:Session

    def __init__(self, config:Dict) -> None:
        """
        Constructor: Connect to and initialise the database session

        :param config:
        :return:
        """
        # Connect to database and instantiate models
        self.log(logging.DEBUG, "Connecting to PostgreSQL database \"{name}\" at {host}:{port}".format(**config))
        self._engine = create_engine("postgresql://{user}:{passwd}@{host}:{port}/{name}".format(**config))
        Base.metadata.create_all(self._engine)

        # Start session (and register close on exit)
        Session = sessionmaker(bind=self._engine)
        self._session = Session()
        atexit.register(self._session.close)

        self._create_minimal()

    def _create_minimal(self) -> None:
        """
        Create minimal data in the database for a working system

        TODO Functions in the functions module should be subsumed as
        more generic methods of this class
        """
        # Set up the e-mail template placeholders for rotation
        # invitations, if they don't already exist
        for template in ROTATION_TEMPLATE_IDS:
            if not self.get_template_by_name(template):
                self._session.add(EmailTemplate(name=template,
                                                subject=f"Placeholder subject for {template}",
                                                content=f"Placeholder content for {template}"))

        # TODO Tidy the below up / set the defaults more appropriately

        if not self.get_all_users():
            self.log(logging.INFO, "No users found. Adding admins.")
            _admin_args = {"user_type": "grad_office", "priority": 0}
            self._session.add(User(name="Simon Beal",    email="sb48@sanger.ac.uk", **_admin_args))
            self._session.add(User(name="Carl Anderson", email="ca3@sanger.ac.uk",  **_admin_args))

        if not self._session.query(ProjectGroup).all():
            self.log(logging.INFO, "No groups found. Adding rotation 1 2017.")
            self._session.add(ProjectGroup(series=2017,
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

    ## E-Mail Template Methods #########################################

    def get_template_by_name(self, name:str) -> Optional[EmailTemplate]:
        """
        Get an e-mail template by its name

        :param name:
        :return:
        """
        q = self._session.query(EmailTemplate)
        return q.filter(EmailTemplate.name == name) \
                .first()

    def get_all_templates(self) -> List[EmailTemplate]:
        """
        Get all e-mail templates in the system

        :return:
        """
        return self._session.query(EmailTemplate) \
                            .order_by(EmailTemplate.name) \
                            .all()

    ## Project Methods #################################################

    def get_project_by_id(self, project_id:int) -> Optional[Project]:
        """
        Get a project by its ID

        :param project_id:
        :return:
        """
        q = self._session.query(Project)
        return q.filter(Project.id == project_id) \
                .first()

    def get_project_by_name(self, project_name:str) -> Optional[Project]:
        """
        Get the newest project by its name

        TODO Do we need this? Fetching something by an arbitrary string
        (i.e., non-key) seems like a bit of an antipattern...

        :param project_name:
        :return:
        """
        q = self._session.query(Project)
        return q.filter(Project.title == project_name) \
                .order_by(desc(Project.id)) \
                .first()

    @overload
    def get_projects_by_student(self, student:User, group:None) -> List[Project]:
        ...
    @overload
    def get_projects_by_student(self, student:User, group:ProjectGroup) -> Optional[Project]:
        ...
    def get_projects_by_student(self, student, group = None):
        """
        Get the list of projects for the specified student or, if a
        project group is specified, that student's project in that group

        :param student:
        :param group:
        :return:
        """
        q = self._session.query(Project)

        clause = (Project.student == student)
        if group:
            clause &= (Project.group == group)

        projects = q.filter(clause).order_by(Project.id)

        if group:
            return projects.first()

        return projects.all()

    def get_projects_by_supervisor(self, supervisor:User, group:Optional[ProjectGroup] = None) -> List[Project]:
        """
        Get the list of projects set by the specified supervisor,
        optionally restricted to a given project group

        :param supervisor:
        :param group:
        :return:
        """
        q = self._session.query(Project)

        clause = (Project.supervisor == supervisor)
        if group:
            clause &= (Project.group == group)

        return q.filter(clause) \
                .order_by(Project.id) \
                .all()

    def get_projects_by_cogs_marker(self, cogs_marker:User, group:Optional[ProjectGroup] = None) -> List[Project]:
        """
        Get the list of projects set by the specified CoGS marker,
        optionally restricted to a given project group

        :param cogs_marker:
        :param group:
        :return:
        """
        q = self._session.query(Project)

        clause = (Project.cogs_marker == cogs_marker)
        if group:
            clause &= (Project.group == group)

        return q.filter(clause) \
                .order_by(Project.id) \
                .all()

    ## Project Group Methods ###########################################

    def get_project_group(self, series:int, part:int) -> Optional[ProjectGroup]:
        """
        Get the project group for the specified series and part

        :param series:
        :param part:
        :return:
        """
        q = self._session.query(ProjectGroup)
        return q.filter(
                 (ProjectGroup.series == series) & (ProjectGroup.part == part)
               ).first()

    def get_project_groups_by_series(self, series:int) -> List[ProjectGroup]:
        """
        Get all project groups for the specified series

        :param series:
        :return:
        """
        q = self._session.query(ProjectGroup)
        return q.filter(ProjectGroup.series == series) \
                .order_by(ProjectGroup.part) \
                .all()

    def get_most_recent_group(self) -> Optional[ProjectGroup]:
        """
        Get the most recently created project group

        :return ProjectGroup:
        """
        q = self._session.query(ProjectGroup)
        return q.order_by(desc(ProjectGroup.id)) \
                .first()

    ## User Methods ####################################################

    def get_user_by_id(self, uid:int) -> Optional[User]:
        """
        Get a user by their ID

        :param uid:
        :return:
        """
        q = self._session.query(User)
        return q.filter(User.id == uid) \
                .first()

    def get_user_by_email(self, email:str) -> Optional[User]:
        """
        Get a user by their e-mail address

        :param email:
        :return:
        """
        q = self._session.query(User)
        return q.filter(User.email == email) \
                .first()

    def get_all_users(self) -> List[User]:
        """
        Get all users in the system

        :return:
        """
        return self._session.query(User).all()
