from aiohttp.web import Application, Request, StreamResponse, middleware
from cogs.common.types import Handler
import logging 

logger=logging.getLogger()
import asyncio

from contextvars import ContextVar

_context = ContextVar("_context", default= "default")


@middleware
async def create_session(request: Request, handler: Handler) -> StreamResponse:
    print("Create Session Middleware ")
    db = request.app["db"]
    Session = db.session
    Session.remove()
    s = Session()
    print(f"Session at creation time {s}")
    return await handler(request)
    



@middleware
async def remove_session(request: Request, handler: Handler) -> StreamResponse:
    print("Remove Session Middleware Called")
    response = await handler(request)
    db = request.app["db"] 
    Session = db.session
    s = Session()
    print(f"Session at removal time {s}")
    Session.remove()
    print("Remove Session Middleware Ended")
    return response