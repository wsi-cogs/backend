from aiohttp_jinja2 import template
from db import User


@template('user_overview.jinja2')
async def user_overview(request):
    session = request.app["session"]
    users = session.query(User).all()
    columns = User.__table__.columns.keys()
    return {"columns": columns,
            "users": ((getattr(user, column) for column in columns) for user in users)}

