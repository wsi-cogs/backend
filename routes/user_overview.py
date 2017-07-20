from aiohttp_jinja2 import template
from db import User


@template('user_overview.jinja2')
async def user_overview(request):
    """
    Show an overview of all registered users as well as a permissions editor.
    This view should only be able to be requested by Grad Office users.

    :param request:
    :return:
    """
    session = request.app["session"]
    users = session.query(User).all()
    columns = User.__table__.columns.keys()
    return {"headers": columns,
            "users": ((getattr(user, column) for column in columns) for user in users)}

