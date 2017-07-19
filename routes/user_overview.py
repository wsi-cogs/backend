from aiohttp import web
from db import User


async def user_overview(request):
    session = request.app["session"]
    users = session.query(User).all()
    return web.Response(text=f"{users}")

