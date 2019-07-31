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
from smtplib import SMTP
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, NamedTuple

from jinja2 import FileSystemLoader, Environment, Template
import natural.number

from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import User
from .constants import DEADLINE_EXTENSION_TEMPLATE
from .message import TemplatedEMail


def to_ordinal(value) -> str:
    return natural.number.ordinal(value)


class _Server(NamedTuple):
    """ Server type """
    host:str
    port:int
    timeout:int


class Postman(logging.LogWriter):
    """ E-mail sender """
    _database:Database
    _server:_Server
    _sender:str
    _templates:Dict[str, Template]
    _threadpool:ThreadPoolExecutor
    environment: Environment

    def __init__(self, database:Database, host:str, port:int, timeout:int, sender:str, bcc: str, url: str) -> None:
        """
        Constructor
        """
        self._database = database

        self._server = _Server(host, port, timeout)
        self._sender = sender
        self._bcc = bcc
        self._url = url

        # Load the filesystem e-mail templates into memory
        fs_loader = FileSystemLoader("cogs/mail/templates")
        self.environment = Environment(loader=fs_loader)
        self.environment.filters["ordinal"] = to_ordinal
        self.environment.filters["st"] = to_ordinal
        self.environment.filters["nd"] = to_ordinal
        self.environment.filters["rd"] = to_ordinal
        self.environment.filters["th"] = to_ordinal
        self._templates = {
            template: self.environment.get_template(template)
            for template in fs_loader.list_templates()
        }

        # We use a threadpool, rather than asyncio
        self._threadpool = ThreadPoolExecutor()
        atexit.register(self._threadpool.shutdown)

    def _email_from_db_template(self, template:str, has_extension:bool = False) -> TemplatedEMail:
        """
        Create templated e-mail based on the specific rotation template
        from the database
        """
        email_template = self._database.get_template_by_name(template)
        if email_template is None:
            return None

        # FIXME? Leaky abstraction
        extension_template = DEADLINE_EXTENSION_TEMPLATE if has_extension else ""

        subject_template = self.environment.from_string(email_template.subject)
        body_template = self.environment.from_string(extension_template + email_template.content)

        return TemplatedEMail(subject_template, body_template)

    def send(self, user:User, template:str, *attachments:str, **context) -> None:
        """
        Prepare the e-mail by template and context and submit it to the
        threadpool to send to the user
        """
        assert isinstance(user, User), user
        self.log(logging.DEBUG, f"Preparing e-mail from \"{template}\" template")

        has_extension = context.get("extension", False)
        mail = self._email_from_db_template(template, has_extension)
        if mail is None:
            # Should never happen
            mail = TemplatedEMail(self._templates[f"{template}_subject.jinja2"],
                                  self._templates[f"{template}_contents.jinja2"])

        mail.sender = self._sender
        mail.recipient = user.best_email
        mail.bcc = self._bcc

        for attachment in attachments:
            mail.add_attachment(attachment)

        mail.set_context("user", user)
        for k, v in context.items():
            mail.set_context(k, v)
        mail.set_context("web_service", self._url)

        self._threadpool.submit(self._send_mail, mail).add_done_callback(self._on_done)

    def _send_mail(self, mail:TemplatedEMail) -> None:
        """
        Render the prepared e-mail and send
        """
        with SMTP(*self._server) as smtp:
            self.log(logging.DEBUG, f"Sending e-mail to {mail.recipient}")
            smtp.send_message(mail.render())

    def _on_done(self, future):
        # Propagate exceptions to main thread
        future.result()


def get_filesystem_templates(exclude=[]):
    def read_file(fn):
        with open(f"cogs/mail/templates/{fn}.jinja2") as f:
            return f.read()

    fs_loader = FileSystemLoader("cogs/mail/templates")
    template_list = [i.replace("_contents", "") for i in
                        (fn.replace(".jinja2", "") for fn in fs_loader.list_templates())
                     if i.endswith("_contents")]
    return [(name, read_file(f"{name}_subject"), read_file(f"{name}_contents")) for name in template_list if name not in exclude]
