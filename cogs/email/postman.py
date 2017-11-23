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
from typing import Dict, List, NamedTuple, Optional

# from bleach import clean
from jinja2 import FileSystemLoader, Environment, Template

from cogs.common import logging
from cogs.common.constants import ROTATION_TEMPLATE_IDS
from cogs.db.interface import Database
from cogs.db.models import User
from .constants import DEADLINE_EXTENSION_TEMPLATE
from .message import TemplatedEMail


class _Server(NamedTuple):
    """ Server type """
    host:str
    port:int


class Postman(logging.LogWriter):
    """ E-mail sender """
    _database:Database
    _server:_Server
    _sender:str
    _templates:Dict[str, Template]
    _threadpool:ThreadPoolExecutor

    def __init__(self, database:Database, host:str, port:int, sender:str) -> None:
        """
        Constructor

        :param database:
        :param host:
        :param port:
        :param sender:
        :return:
        """
        # Initialise logger
        super().__init__()

        self._database = database

        self._server = _Server(host, port)
        self._sender = sender

        # Load the filesystem e-mail templates into memory
        fs_loader = FileSystemLoader("cogs/email/templates")
        fs_env = Environment(loader=fs_loader)
        self._templates = {
            template: fs_env.get_template(template)
            for template in fs_loader.list_templates()
        }

        # We use a threadpool, rather than asyncio
        self._threadpool = ThreadPoolExecutor()
        atexit.register(self._threadpool.shutdown)

    def _email_from_db_template(self, template:str, has_extension:bool = False) -> TemplatedEMail:
        """
        Create templated e-mail based on the specific rotation template
        from the database

        :param template:
        :param has_extension:
        :return:
        """
        email_template = self._database.get_template_by_name(template)

        # FIXME? Leaky abstraction
        extension_template = DEADLINE_EXTENSION_TEMPLATE if has_extension else ""

        subject_template = Template(email_template.subject)
        body_template = Template(extension_template + email_template.body)

        return TemplatedEMail(subject_template, body_template)

    def send(self, user:User, template:str, attachments:Optional[List[str]] = None, **context) -> None:
        """
        Prepare the e-mail by template and context and submit it to the
        threadpool to send to the user

        :param user:
        :param template:
        :param attachments:
        :return:
        """
        self.log(logging.DEBUG, "Preparing e-mail from \"{template}\" template")

        if template in ROTATION_TEMPLATE_IDS:
            has_extension = context.get("extension", False)
            mail = self._email_from_db_template(template, has_extension)
        else:
            mail = TemplatedEMail(self._templates[f"{template}_subject.jinja2"],
                                  self._templates[f"{template}_contents.jinja2"])

        mail.sender = self._sender
        mail.recipient = user.email

        for attachment in attachments or []:
            mail.add_attachment(attachment)

        for k, v in context.items():
            mail.set_context(k, v)

        self._threadpool.submit(self._send_mail, mail)

    def _send_mail(self, mail:TemplatedEMail) -> None:
        """
        Render the prepared e-mail and send

        :param mail:
        :return:
        """
        with SMTP(*self._server) as smtp:
            self.log(logging.DEBUG, f"Sending e-mail to {mail.recipient}")
            smtp.send_message(mail.render())


# TODO This function is used elsewhere. I haven't checked why, yet.
# def clean_html(html: str) -> str:
#     cleaned = clean(html,
#                     tags=['a', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'font', 'div', 'u', 'pre', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'sub', 'sup', 'span'],
#                     attributes=['align', 'size', 'face', 'href', 'title', 'target'],
#                     strip=True)
#     return cleaned
