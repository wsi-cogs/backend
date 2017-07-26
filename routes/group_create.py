from aiohttp_jinja2 import template
from permissions import view_only


@template("group_create.jinja2")
@view_only("create_project_groups")
async def group_create(request):
    return {}
