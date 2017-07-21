from db import User
from aiohttp import web


async def login(request):
    """
    Log a user into the system and set their permissions
    :param request:
    :return:
    """
    post_req = await request.post()
    user_type = post_req["type"]
    response = web.Response(text=user_type)
    response.set_cookie("user_type", user_type)
    logged_in = True
    if user_type == "admin":
        for perm in next(iter(request.app["permissions"].values())):
            response.set_cookie(perm, True)
    elif user_type == "":
        for perm in next(iter(request.app["permissions"].values())):
            response.del_cookie(perm)
        logged_in = False
        response.del_cookie("user_type")
    else:
        for key, value in request.app["permissions"][user_type].items():
            response.set_cookie(key, value)
    if logged_in:
        session = request.app["session"]
        user = session.query(User).first()
        response.set_cookie("user_id", user.id)
    else:
        response.del_cookie("user_id")
    return response
