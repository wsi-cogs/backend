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
from typing import Dict

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from cogs.common.constants import ROTATION_TEMPLATE_IDS
from . import functions, models


class Database(object):
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
        self._engine = create_engine("postgresql://{user}:{passwd}@{host}:{port}/{name}".format(**config))
        models.Base.metadata.create_all(self._engine)

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
            if not functions.get_template_name(self._session, template):
                self._session.add(models.EmailTemplate(name=template,
                                                       subject=f"Placeholder subject for {template}",
                                                       content=f"Placeholder content for {template}"))

        # TODO Tidy the below up / set the defaults more appropriately

        if not functions.get_all_users(self._session):
            print("No users found. Adding admins.")
            _admin_args = {"user_type": "grad_office", "priority": 0}
            self._session.add(models.User(name="Simon Beal",    email="sb48@sanger.ac.uk", **_admin_args))
            self._session.add(models.User(name="Carl Anderson", email="ca3@sanger.ac.uk",  **_admin_args))

        if not functions.get_all_groups(self._session):
            print("No groups found. Adding rotation 1 2017.")
            self._session.add(models.ProjectGroup(series=2017,
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
