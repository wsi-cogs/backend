from aiohttp import web


async def login(request):
    post_req = await request.post()
    login_type = post_req["type"]
    response = web.Response(text=login_type)
    response.set_cookie("permission_type", login_type)x
    return response
