from aiohttp_jinja2 import template
from project import get_most_recent_group, get_projects_user


@template("user_page.jinja2")
async def user_page(request):
    cookies = request.cookies
    session = request.app["session"]
    group = get_most_recent_group(session)
    rtn = {"can_edit": not group.read_only}
    if cookies["create_projects"] == "True":
        rtn["series_list"] = get_projects_user(request, int(cookies["user_id"]))

    rtn.update(cookies)
    return rtn
