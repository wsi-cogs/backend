from aiohttp_jinja2 import template

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
        for key in post.keys():
            if key in done_keys:
                continue
            done_keys.add(key)
            user_id, column = key.split("_", 1)
            user = get_user_id(session, user_id=int(user_id))
            setattr(user, column, "|".join(post.getall(key)))
    session.commit()
    user_types = request.app["permissions"].keys()
    users = get_all_users(session)
    columns = ("name", "email", "priority", "user_type")
    return {"headers": columns,
            "users": users,
            "user_types": user_types}

