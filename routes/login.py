from aiohttp import web


async def login(request):
    """
    Log a user into the system and set their permissions
    :param request:
    :return:
    """
    post_req = await request.post()
    login_type = post_req["type"]
    response = web.Response(text=login_type)
    response.set_cookie("permission_type", login_type)
    return response
