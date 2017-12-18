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

from typing import Dict

from aiohttp.web import Request, Response
from aiohttp_jinja2 import template

from cogs.common.constants import ROTATION_TEMPLATE_IDS
from cogs.mail import sanitise
from cogs.security.middleware import permit


@permit("create_project_groups")
@template("email_edit.jinja2")
async def email_edit(request:Request) -> Dict:
    """
    Edit an email

    NOTE This handler should only be allowed if the current user has
    "create_projects" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    return {
        "templates": db.get_all_templates(),
        "cur_option": "email_edit",
        **navbar_data}


@permit("create_project_groups")
async def on_edit(request:Request) -> Response:
    """
    Update the e-mail template

    NOTE This handler should only be allowed if the current user has
    "create_projects" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    post = await request.post()

    template_name = post["name"]
    assert template_name in ROTATION_TEMPLATE_IDS

    template = db.get_template_by_name(template_name)
    template.subject = post["subject"]
    template.content = sanitise(post["data"])
    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text=f"/email_edit")
