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

from aiohttp.web import Request
from aiohttp_jinja2 import template

from cogs.common.constants import PROGRAMMES


@template("project_edit.jinja2")
def resubmit(request:Request) -> Dict:
    """
    TODO Docstring

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    project_id = int(request.match_info["project_id"])
    project = db.get_project_by_id(project_id)

    return {
        "project":    project,
        "label":      "Submit",
        "programmes": PROGRAMMES,
        "cur_option": "create_project",
        **navbar_data}
