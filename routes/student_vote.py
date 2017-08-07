from aiohttp import web
from permissions import view_only, value_set


@view_only("join_projects")
@value_set("student_choosable")
async def on_submit(request):
    post = await request.post()
    print(post)

    return web.Response(status=200, text=f"set")
