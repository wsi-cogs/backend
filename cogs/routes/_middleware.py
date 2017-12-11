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

from datetime import date
from typing import Dict

from aiohttp.web import Application, Request, Response

from cogs.auth.dummy import DummyAuthenticator
from cogs.common.types import Handler
from cogs.scheduler.constants import DEADLINES
from cogs.security.model import Role


async def navbar_data(app:Application, handler:Handler) -> Handler:
    """
    Navigation bar data setup middleware factory

    :param app:
    :param handler:
    :return:
    """
    db = app["db"]

    root_map:Dict[str, str] = {
        "join_projects":         "My Choices",
        "create_projects":       "My Owned Projects",
        "create_project_groups": "Rotations"}

    show_login_bar = isinstance(app["auth"], DummyAuthenticator)

    # TODO I feel this should be put somewhere else...
    show_mark_projects = Role(
        modify_permissions          = False,
        create_project_groups       = False,
        set_readonly                = False,
        create_projects             = True,
        review_other_projects       = True,
        join_projects               = False,
        view_projects_predeadline   = False,
        view_all_submitted_projects = False)

    async def _middleware(request:Request) -> Response:
        """
        Navigation bar data setup middleware, threading the data to
        drive the navigation bar through the request under the "navbar"
        key

        FIXME This is pretty messy...

        :param request:
        :return:
        """
        group = db.get_most_recent_group()
        series_groups = db.get_project_groups_by_series(group.series)
        user = request["user"]

        # TODO Use a named tuple, rather than this big dictionary
        # Either that, or just thread each key through the request
        data = {
            "can_edit":              not group.read_only,
            "deadlines":             DEADLINES,  # FIXME? Is this needed?
            "display_projects_link": user.can_view_group(group),
            "user":                  user,  # FIXME We don't need this, any more
            "permissions":           user.role,  # FIXME ...Likewise, this isn't necessary
            "show_login_bar":        show_login_bar,
            "show_mark_projects":    show_mark_projects & user.role}

        # FIXME This is nasty!
        data["root_title"] = \
            ", ".join(v for p, v in root_map.items() if getattr(user.role, p)) \
            or ("Assigned Projects" if user.role.review_other_projects else "Main Page")

        if user.role.view_all_submitted_projects:
            # All series
            # TODO? Can this be done once, rather than on each request?
            data["series_years"] = db.get_all_series()

            # Project groups in this series
            data["rotations"] = list(map(lambda g: g.part, series_groups))

        data["show_submit"] = False
        if user.role.join_projects:
            project = db.get_projects_by_student(user, group)
            if project and group.student_uploadable and not project.grace_passed:
                data["show_submit"] = True

        if user.role.create_project_groups:
            # FIXME? Why not just thread through the list of groups,
            # rather than reducing them to their dates?
            data["groups"] = list(map(lambda g: g.dates, series_groups))

            if group.student_choice < date.today():
                data["show_create_rotation"] = True

        if user.role.set_readonly:
            # FIXME This would be redundant if we threaded through the group
            data["show_finalise_choices"] = group.can_finalise

        request["navbar"] = data
        return await handler(request)

    return _middleware
