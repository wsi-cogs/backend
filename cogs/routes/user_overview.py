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
                # The type of dictionary given supports duplicate values for each key.
                # This means we need to skip keys we've already handled
                continue

            done_keys.add(key)
            # Each key is in the form "`user_id`_`database_field`"
            user_id, column = key.split("_", 1)
            # If the key was sent multiple times, create a single string with it's pipe separated value
            # This means all values are interpreted as strings
            user_map[int(user_id)][column] = "|".join(post.getall(key)).strip()

        for user_id, columns in user_map.items():
            # Default priority to 0 if not passed
            columns = {
                "priority": "0",
                **columns}

            # If these fields aren't as expected, don't save them
            # Name and email are required and priority needs to be an integer
            if not columns["name"] \
                or not columns["email"] \
                or not columns["priority"].isnumeric():
                continue

            # Anyone with permissions to set them must be grad office
            # This is an assumption that roles won't change though
            if "user_type" not in columns:
                columns["user_type"] = "grad_office" if user_id == user.id else ""
            elif user_id == user.id:
                columns["user_type"] += "|grad_office"

            # Priority is stored as an int and can overflow, crashing the db. Limit to sensible real world limits
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

        # n.b., Changing your own user role will not affect the navbar data in this request and you'd be forced to
        # reload to update the navbar. This shouldn't happen in real life.

    role_list = [role for role in dir(roles) if isinstance(getattr(roles, role), Role) and role != "zero"]

    return {
        "headers":    ("name", "email", "priority", "user_type"),
        "users":      db.get_all_users(),
        "user_types": role_list,
        "logged_in":  user.id,  # For clarity purposes in the template
        "cur_option": "edit_users",
        **navbar_data}
