import glob
import os

import aiofiles
from aiohttp import web
from aiohttp_jinja2 import template

from db_helper import get_user_cookies, get_most_recent_group
from permissions import view_only


@template('student_upload.jinja2')
async def student_upload(request):
    return {}


@view_only("join_projects")
async def on_submit(request):
    return web.json_response({"success": True})
    session = request.app["session"]
    group = get_most_recent_group(session)
    cookies = request.cookies
    post = await request.post()
    uploaded = post["file_data"]
    extension = uploaded.filename.rsplit(".", 1)[1][:4]
    user_id = get_user_cookies(cookies)
    user_path = os.path.join("upload", str(user_id))
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    filename = os.path.join(user_path, f"{group.series}_{group.part}.")
    existing_files = glob.glob(filename+"*")
    if existing_files:
        if post["force"] == "true":
            for path in existing_files:
                os.remove(path)
        else:
            return web.Response(status=403, text="A file has already been uploaded for this project")
    async with aiofiles.open(filename+extension, mode="wb") as f:
        await f.write(uploaded.file.read())
    return web.json_response({"success": True})

async def on_check(request):
    session = request.app["session"]
    cookies = request.cookies
    group = get_most_recent_group(session)
    user_id = get_user_cookies(cookies)
    user_path = os.path.join("upload", str(user_id))
    if os.path.exists(user_path):
        filename = os.path.join(user_path, f"{group.series}_{group.part}.")
        existing_files = glob.glob(filename + "*")
        if existing_files:
            return web.json_response({"must_force": True})
    return web.json_response({"must_force": False})
