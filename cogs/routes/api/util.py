from asyncio import get_running_loop
from datetime import datetime
import time

from aiohttp.web import Request, Response
from ._format import HTTPError, match_info_to_id


async def get_status(request: Request) -> Response:
    """Return a custom status."""
    status = match_info_to_id(request, "status")
    raise HTTPError(status=status, message=str(status))


async def get_time(request: Request) -> Response:
    """Return the web server's idea of the current time.

    Useful in development mode when libfaketime is being used.
    """
    return Response(text=f"""\
   datetime.now(): {datetime.now()}
      time.time(): {time.time()}
event_loop.time(): {get_running_loop().time()}
""")
