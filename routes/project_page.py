from aiohttp import web
from db import User, Project


async def project(request):
    user_name = request.match_info['user_name']
    session = request.app["session"]
    query = session.query(User).filter_by(name=user_name)
    user = query.first()
    projects = session.query(Project).filter_by(supervisor=user.id).all()
    return web.Response(text=f"{user}<br>{projects}")

