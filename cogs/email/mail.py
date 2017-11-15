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

# import aiofiles
# from aiohttp.web import Application
# from bleach import clean
# from jinja2 import Environment, BaseLoader

import atexit
from smtplib import SMTP
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, NamedTuple, Optional

from jinja2 import FileSystemLoader, Environment, Template

from cogs.common.constants import ROTATION_TEMPLATE_IDS
from cogs.db.models import User
from .message import TemplatedEMail


class _Server(NamedTuple):
    """ Server type """
    host:str
    port:int


def _email_from_db_template(template:str) -> TemplatedEMail:
    """
    Fetch rotation template from the database

    :param template:
    :return:
    """

class Mailer(object):
    """ E-mail sender """
    _server:_Server
    _sender:str
    _templates:Dict[str, Template]
    _threadpool:ThreadPoolExecutor

    def __init__(self, host:str, port:int, sender:str) -> None:
        """
        Constructor

        :param host:
        :param port:
        :param sender:
        :return:
        """
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

    def send(self, user:User, template:str, attachments:Optional[List[str]] = None, **context) -> None:
        """
        Prepare the e-mail by template and context and submit it to the
        threadpool to send to the user

        :param user:
        :param template:
        :param attachments:
        :return:
        """
        if template in ROTATION_TEMPLATE_IDS:
            mail = _email_from_db_template(template)
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
            smtp.send_message(mail.render())




## async def send_user_email(app: Application, user: str, template_name: str, attachments: Optional[Dict[str, str]]=None, **kwargs):
##     config = app["config"]["email"]
##     web_config = app["config"]["webserver"]
## 
##     extra_content = ""
##     if kwargs.get("extension", False) is True:
##         extra_content = "The deadline has been extended to {{ new_deadline.strftime('%d/%m/%Y') }} due to not enough projects being submitted.<br><br><hr><br>"
## 
##     contents = {}
##     if template_name in app["config"]["misc"]["email_whitelist"]:
##         template = functions.get_template_name(app["session"], template_name)
##         env = Environment(loader=BaseLoader).from_string(template.subject.replace("\n", ""))
##         contents["subject"] = env.render(config=config, user=user, web_config=web_config, **kwargs)
##         env = Environment(loader=BaseLoader).from_string(extra_content+template.content.replace("\n", ""))
##         contents["contents"] = env.render(config=config, user=user, web_config=web_config, **kwargs)
##     else:
##         for message_type in ("subject", "contents"):
##             async with aiofiles.open(f"cogs/email_templates/{template_name}_{message_type}.jinja2") as template_f:
##                 env = Environment(loader=BaseLoader).from_string((await template_f.read()).replace("\n", ""))
##             rendered = env.render(config=config, user=user, web_config=web_config, **kwargs)
##             contents[message_type] = rendered
## 
## 
## def clean_html(html: str) -> str:
##     cleaned = clean(html,
##                     tags=['a', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'font', 'div', 'u', 'pre', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'sub', 'sup', 'span'],
##                     attributes=['align', 'size', 'face', 'href', 'title', 'target'],
##                     strip=True)
##     return cleaned
