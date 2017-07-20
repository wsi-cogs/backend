from aiohttp_jinja2 import template


@template('user_overview.jinja2')
async def index(request):
    return {}

