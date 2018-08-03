"""
Copyright (c) 2017, 2018 Genome Research Ltd.

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

from aiohttp.web import Request, Response, HTTPForbidden, HTTPInternalServerError
from aiohttp_jinja2 import template

from cogs.common.constants import GRADES
from cogs.db.models import ProjectGrade
from cogs.mail import sanitise
from cogs.security.middleware import permit


@template("project_grade.jinja2")
async def project_grade(request: Request) -> Dict:
    """
    Show a student their grade

    :param request:
    :return:
    """
    return request["navbar"]
