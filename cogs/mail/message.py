"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
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

import os.path
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

from jinja2 import Template

from cogs.common import HTMLRenderer


_render_html = HTMLRenderer()


class TemplatedEMail(object):
    """ E-mail message generated from template """
    _sender:str
    _recipient:str
    _bcc: Optional[str]
    _subject_template:Template
    _body_template:Template
    _attached_files:List[str]  # List of filenames, which are loaded on expansion
    _context:Dict

    def __init__(self, subject:Template, body:Template, signature: str = "") -> None:
        """
        Construct e-mail from templates
        """
        self._subject_template = subject
        self._body_template = body
        self._attached_files = []
        self._context = {}
        self.bcc = None
        self._signature = signature

    def render(self) -> EmailMessage:
        """ Render the e-mail message in full """
        assert self._recipient and self._sender

        mail = EmailMessage()
        mail["To"] = self._recipient
        mail["From"] = self._sender
        if self._bcc is not None:
            mail["Bcc"] = self._bcc

        mail["Subject"] = self._subject_template.render(**self._context).rstrip()

        html_body = self._body_template.render(**self._context) + self._signature
        text_body = _render_html(html_body)

        mail.set_content(text_body)
        mail.add_alternative(html_body, subtype="html")

        for attachment in self._attached_files:
            with open(attachment, "rb") as data:
                mail.add_attachment(data.read(),
                                    filename=os.path.basename(attachment),
                                    maintype="application",
                                    subtype="octet-stream")
        return mail

    @property
    def sender(self) -> str:
        return self._sender

    @sender.setter
    def sender(self, address:str) -> None:
        self._sender = address

    @property
    def recipient(self) -> str:
        return self._recipient

    @recipient.setter
    def recipient(self, address:str) -> None:
        self._recipient = address

    @property
    def bcc(self) -> Optional[str]:
        return self._bcc

    @bcc.setter
    def bcc(self, address: Optional[str]) -> None:
        self._bcc = address

    def add_attachment(self, attachment:str) -> None:
        self._attached_files.append(attachment)

    def set_context(self, key:str, value:Any) -> None:
        self._context[key] = value
