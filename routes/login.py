from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from db_helper import get_user_id


async def login(request: Request) -> Response:
    """
    Log a user into the system and set their permissions

    :param request:
    :return:
    """
    post_req = await request.post()
    user_type = post_req["type"]
    response = web.Response(text=user_type)
    if user_type == "":
        response.del_cookie("user_id")
    else:
        session = request.app["session"]
        user = get_user_id(session, user_id=1)
        user.user_type = user_type
        session.commit()
        response.set_cookie("user_id", user.id)
    return response
