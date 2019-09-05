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
from os import PathLike
from typing import Collection, Dict, NamedTuple, Optional, Sequence, Sized, Union

import inflect
from jinja2 import FileSystemLoader, Environment, Template

from cogs.common import logging
from cogs.db.interface import Database
from cogs.db.models import User
from .constants import SIGNATURE
from .message import TemplatedEMail


def to_ordinal(value) -> str:
    """Turn a (cardinal) number into a string.

    >>> to_ordinal(1)
    '1st'
    >>> to_ordinal(4)
    '4th'
    """
    return inflect.engine().ordinal(value)


def report_list(part: int) -> Sequence[str]:
    """Decide which things students must submit for a rotation.

    You probably want to use report_or_poster() instead; this is mostly
    for use with plural_verb(), plural_noun() etc.
    """
    if part == 2:
        return ["abstract", "poster"]
    return ["report"]


def report_or_poster(part: int) -> str:
    """Return a string of things students must submit for a rotation."""
    return " and ".join(report_list(part))


def plural_verb(verb: str, n: Union[int, Sized]) -> str:
    """Pluralise a verb based on a number or the length of a sequence."""
    if not isinstance(n, int):
        n = len(n)
    return inflect.engine().plural_verb(verb, n)


def plural_noun(noun: str, n: Union[int, Sized]) -> str:
    """Pluralise a noun based on a number or the length of a sequence."""
    if not isinstance(n, int):
        n = len(n)
    return inflect.engine().plural_noun(noun, n)


class _Server(NamedTuple):
    """SMTP server connection details."""
    host: str
    port: int
    timeout: int


class Postman(logging.LogWriter):
    """E-mail sender."""

    _database: Database
    _server: _Server
    _sender: str
    _templates: Dict[str, Template]
    _threadpool: ThreadPoolExecutor
    environment: Environment

    def __init__(self, database: Database, host: str, port: int, timeout: int, sender: str, bcc: str, url: str) -> None:
        self._database = database

        self._server = _Server(host, port, timeout)
        self._sender = sender
        self._bcc = bcc
        self._url = url
        self._signature = SIGNATURE.format(web_service=url)

        # Load the filesystem e-mail templates into memory
        fs_loader = FileSystemLoader("cogs/mail/templates")
        self.environment = Environment(loader=fs_loader)
        self.environment.filters["ordinal"] = to_ordinal
        self.environment.filters["st"] = to_ordinal
        self.environment.filters["nd"] = to_ordinal
        self.environment.filters["rd"] = to_ordinal
        self.environment.filters["th"] = to_ordinal
        self.environment.filters["plural_verb"] = plural_verb
        self.environment.filters["plural_noun"] = plural_noun
        self.environment.globals["report_list"] = report_list
        self.environment.globals["report_or_poster"] = report_or_poster
        self._templates = {
            template: self.environment.get_template(template)
            for template in fs_loader.list_templates()
        }

        # We use a threadpool, rather than asyncio
        self._threadpool = ThreadPoolExecutor()
        # TODO: does this actually do anything useful? (related to #18?)
        atexit.register(self._threadpool.shutdown)

    def _email_from_db_template(self, template: str) -> Optional[TemplatedEMail]:
        """Create an e-mail based on a template from the database."""
        email_template = self._database.get_template_by_name(template)
        if email_template is None:
            return None

        assert email_template.subject is not None
        assert email_template.content is not None
        subject_template = self.environment.from_string(email_template.subject)
        body_template = self.environment.from_string(email_template.content)

        return TemplatedEMail(subject_template, body_template, self._signature)

    def send(self, user: Union[User, Collection[User]], template: str, *attachments: Union[str, PathLike], **context) -> None:
        """Prepare an e-mail from a template and context, then send it.

        If multiple users are passed in the first argument, all users
        but the first will be CC'd (the first will be used in the To:
        header).
        """
        if not isinstance(user, User):
            try:
                user, *cc_users = user
            except ValueError:
                self.log(logging.ERROR, f"No users to email for {template!r}, not sending mail")
                return
        else:
            cc_users = []

        self.log(logging.DEBUG, f"Preparing e-mail from \"{template}\" template for {user.best_email}")

        mail = self._email_from_db_template(template)
        if mail is None:
            # Mail isn't in the DB -- should never happen
            self.log(logging.WARNING, "Template {} not found in DB".format(template))
            mail = TemplatedEMail(
                self._templates[f"{template}_subject.jinja2"],
                self._templates[f"{template}_contents.jinja2"],
                self._signature,
            )

        mail.sender = self._sender
        recipient = user.best_email
        if recipient is None:
            self.log(logging.WARNING, f"No address for user {user.id}, not sending mail")
            return
        mail.recipient = recipient
        mail.cc = ", ".join(u.best_email for u in cc_users if u.best_email is not None) or None
        mail.bcc = self._bcc

        for attachment in attachments:
            mail.add_attachment(attachment)

        mail.set_context("user", user)
        for k, v in context.items():
            mail.set_context(k, v)
        mail.set_context("web_service", self._url)

        self._threadpool.submit(self._send_mail, mail).add_done_callback(self._on_done)

    def _send_mail(self, mail: TemplatedEMail) -> None:
        """Render the prepared e-mail and send it."""
        with SMTP(**self._server._asdict()) as smtp:
            self.log(logging.DEBUG, f"Sending e-mail to {mail.recipient}")
            smtp.send_message(mail.render())

    def _on_done(self, future):
        # Propagate exceptions to main thread
        future.result()


def get_filesystem_templates(exclude=[]):
    """Retrieve all templates found in the filesystem.

    Returns a list of 3-tuples, consisting of:
    - the template's name (e.g. "cogs_not_found")
    - the subject template
    - the contents template
    """
    def read_file(fn):
        with open(f"cogs/mail/templates/{fn}.jinja2") as f:
            return f.read()

    fs_loader = FileSystemLoader("cogs/mail/templates")
    template_list = [i.replace("_contents", "") for i in
                        (fn.replace(".jinja2", "") for fn in fs_loader.list_templates())
                     if i.endswith("_contents")]
    return [(name, read_file(f"{name}_subject"), read_file(f"{name}_contents")) for name in template_list if name not in exclude]
