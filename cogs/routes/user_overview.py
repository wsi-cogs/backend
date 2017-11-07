from collections import defaultdict
from typing import Dict

from aiohttp.web_request import Request
from aiohttp_jinja2 import template

from cogs.db.models import User
from cogs.db.functions import get_all_users, get_user_id, get_user_cookies, get_navbar_data
from permissions import view_only


@template('user_overview.jinja2')
@view_only("modify_permissions")
async def user_overview(request: Request) -> Dict:
    """
    Show an overview of all registered users as well as a permissions editor.
    This view should only be able to be requested by Grad Office users.

    :param request:
    :return:
    """
    logged_in_id = get_user_cookies(request.app, request.cookies)
    session = request.app["session"]
    if request.method == "POST":
        post = await request.post()
        done_keys = set()
        user_map = defaultdict(dict)
        for key in post.keys():
            if key in done_keys:
                continue
            done_keys.add(key)
            user_id, column = key.split("_", 1)
            user_map[user_id][column] = "|".join(post.getall(key))
        for user_id, columns in user_map.items():
            user_id = int(user_id)
            if "user_type" not in columns:
                if user_id == logged_in_id:
                    columns["user_type"] = "grad_office"
                else:
                    columns["user_type"] = ""
            elif user_id == logged_in_id:
                columns["user_type"] += "|grad_office"
            if "priority" not in columns:
                columns["priority"] = "0"
            if not columns["name"].strip():
                continue
            if not columns["email"].strip():
                continue
            if not columns["priority"].isnumeric():
                continue
            columns["priority"] = min((max((0, int(columns["priority"]))), 100))
            user = get_user_id(request.app, user_id=user_id)
            if not user:
                user = User(name=columns["name"],
                            email=columns["email"],
                            priority=columns["priority"],
                            user_type=columns["user_type"])
                session.add(user)
            else:
                user.name = columns["name"]
                user.email = columns["email"]
                user.priority = columns["priority"]
                user.user_type = columns["user_type"]
    columns = ("name", "email", "priority", "user_type")
    session.commit()
    users = get_all_users(session)
    user_types = request.app["config"]["permissions"].keys()
    return {"headers": columns,
            "users": users,
            "user_types": user_types,
            "logged_in": get_user_id(request.app, request.cookies),
            "cur_option": "edit_users",
            **get_navbar_data(request)}

