from collections import defaultdict

from aiohttp_jinja2 import template

from db import User
from db_helper import get_all_users, get_user_id
from permissions import view_only


@template('user_overview.jinja2')
@view_only("modify_permissions")
async def user_overview(request):
    """
    Show an overview of all registered users as well as a permissions editor.
    This view should only be able to be requested by Grad Office users.

    :param request:
    :return:
    """
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
            if "user_type" not in columns:
                columns["user_type"] = ""
            if "priority" not in columns:
                columns["priority"] = "0"
            if not columns["name"].strip():
                continue
            if not columns["email"].strip():
                continue
            if not columns["priority"].isnumeric():
                continue
            columns["priority"] = int(columns["priority"])
            user = get_user_id(session, user_id=int(user_id))
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
    user_types = request.app["permissions"].keys()
    return {"headers": columns,
            "users": users,
            "user_types": user_types}

