from aiohttp.web import Request, Response
from ._format import HTTPError, match_info_to_id


async def get_status(request: Request) -> Response:
    """
    return a custom status

    :param request:
    :return:
    """
    status = match_info_to_id(request, "status")
    return HTTPError(status=status, message=str(status))
