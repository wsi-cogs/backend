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

from collections import defaultdict
from typing import DefaultDict, Dict, Set

from aiohttp.web import Request
from aiohttp_jinja2 import template

from cogs.db.models import User
from cogs.security.middleware import permit
import cogs.security.roles as roles
from cogs.security.model import Role


@permit("modify_permissions")
@template("user_overview.jinja2")
async def user_overview(request:Request) -> Dict:
    """
    Show an overview of all registered users as well as a permissions
    editor

    NOTE This handler should only be able to be requested by Graduate
    Office users

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    navbar_data = request["navbar"]

    if request.method == "POST":
        post = await request.post()

        done_keys:Set[str] = set()
        user_map:DefaultDict[int, Dict[str, str]] = defaultdict(dict)

        for key in post.keys():
            if key in done_keys:
                # FIXME? Dictionary keys ought to be unique, so this
                # should never happen... However, it's POST data, so I
                # bet something weird is happening with duplicate keys
                continue

            # TODO Document the incoming POST data so it's clear that
            # what is happening below is correct
            done_keys.add(key)
            user_id, column = key.split("_", 1)
            user_map[int(user_id)][column] = "|".join(post.getall(key)).strip()

        for user_id, columns in user_map.items():
            # TODO Again, I don't really know what's going on here with
            # regard to what the data represents
            columns = {
                "priority": "0",
                **columns}

            if not columns["name"] \
                or not columns["email"] \
                or not columns["priority"].isnumeric():
                continue

            if "user_type" not in columns:
                columns["user_type"] = "grad_office" if user_id == user.id else ""

            elif user_id == user.id:
                columns["user_type"] += "|grad_office"

            columns["priority"] = min(max(0, int(columns["priority"])), 100)

            edit_user = db.get_user_by_id(user_id)
            if not edit_user:
                # Insert new user
                edit_user = User(
                    name      = columns["name"],
                    email     = columns["email"],
                    priority  = columns["priority"],
                    user_type = columns["user_type"])

                db.add(edit_user)

            else:
                # Update existing user
                edit_user.name      = columns["name"]
                edit_user.email     = columns["email"]
                edit_user.priority  = columns["priority"]
                edit_user.user_type = columns["user_type"]

        # Commit all changes in POST
        db.commit()

    role_list = [role for role in dir(roles) if isinstance(getattr(roles, role), Role) and role != "zero"]

    return {
        "headers":    ("name", "email", "priority", "user_type"),
        "users":      db.get_all_users(),
        "user_types": role_list,
        "logged_in":  user.id,  # FIXME Is this necessary?
        "cur_option": "edit_users",
        **navbar_data}
