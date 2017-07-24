from aiohttp_jinja2 import template
from project import get_most_recent_group, get_group, get_series


@template("user_page.jinja2")
async def user_page(request):
    cookies = request.cookies
    session = request.app["session"]
    group = get_most_recent_group(session)

    rtn = {"can_edit": not group.read_only}
    rtn.update(cookies)
    return rtn
