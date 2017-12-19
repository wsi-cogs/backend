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

from datetime import datetime, date, timedelta
from typing import Dict, Tuple

from aiohttp.web import Request, Response, HTTPForbidden
from aiohttp_jinja2 import template

from cogs.db.models import ProjectGroup
from cogs.scheduler.constants import GROUP_DEADLINES
from cogs.security.middleware import permit


@permit("create_project_groups")
@template("group_create.jinja2")
async def group_create(request:Request) -> Dict:
    """
    Show the form for creating a new group

    NOTE This handler should only be allowed if the current user has
    "create_project_groups" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    navbar_data = request["navbar"]

    group = db.get_most_recent_group()
    series, part = _get_next_series_group(group)

    if group.student_choice >= date.today():
        raise HTTPForbidden(text="Can't create rotation while the current one is still in the student choice phase.")

    new_group = ProjectGroup(part=part)
    today = date.today()

    for i, deadline in enumerate(GROUP_DEADLINES, 1):
        setattr(new_group, deadline, today+timedelta(days=i))

    return {
        "group":      new_group,
        "deadlines":  GROUP_DEADLINES,
        "cur_option": "create_rotation",
        **navbar_data}


@permit("create_project_groups")
async def on_create(request:Request) -> Response:
    """
    Create a new project group

    NOTE This handler should only be allowed if the current user has
    "create_project_groups" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    scheduler = request.app["scheduler"]

    group = db.get_most_recent_group()
    series, part = _get_next_series_group(group)

    post = await request.post()

    for deadline in GROUP_DEADLINES:
        assert deadline in post and post[deadline], f"The {deadline} deadline was not set"

    deadlines = {
        deadline: datetime.strptime(post[deadline], "%d/%m/%Y")
        for deadline in GROUP_DEADLINES}

    new_group = ProjectGroup(
        series       = series,
        part         = part,
        read_only    = False,
        can_finalise = False,
        **deadlines)

    db.add(new_group)
    group.read_only = True
    db.commit()

    for deadline_id, time in deadlines.items():
        scheduler.schedule_deadline(time, deadline_id, new_group)

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="/")


@permit("create_project_groups")
async def on_modify(request:Request) -> Response:
    """
    Modify the most recent project group

    NOTE This handler should only be allowed if the current user has
    "create_project_groups" permissions

    :param request:
    :return:
    """
    db = request.app["db"]
    mail = request.app["mailer"]
    scheduler = request.app["scheduler"]

    part = int(request.match_info["group_part"])
    most_recent = db.get_most_recent_group()
    group = db.get_project_group(most_recent.series, part)

    post = await request.post()

    for key, value in post.items():
        time = datetime.strptime(value, "%d/%m/%Y").date()

        if key == "supervisor_submit" and time != group.supervisor_submit:
            for supervisor in db.get_users_by_permission("create_projects"):
                mail.send(supervisor, f"supervisor_invite_{group.part}", new_deadline=time, extension=True)

        setattr(group, key, time)

        if time > date.today():
            scheduler.schedule_deadline(time, key, group)

        if key == "student_choice":
            group.student_choosable = time > date.today()

    db.commit()

    # TODO This doesn't seem like an appropriate response...
    return Response(status=200, text="/")


def _get_next_series_group(group:ProjectGroup) -> Tuple[int, int]:
    """
    TODO Docstring

    FIXME I can let the golfiness of this slide, but it assumes that a
    series is always made up of three parts. That's not an unreasonable
    assumption -- and it's not likely to change -- but it effectively
    hardcodes this "detail" into the system. Ideally, everything like
    this ought to be data-driven, where the data model is fluid enough
    to adapt to change.

    :param group:
    :return:
    """
    series = group.series + group.part // 3
    part = (group.part % 3) + 1
    return series, part
