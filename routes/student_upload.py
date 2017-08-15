import glob
import os

import aiofiles
from aiohttp import web
from aiohttp_jinja2 import template

from db_helper import get_user_cookies, get_most_recent_group, get_project_id
from permissions import view_only, get_permission_from_cookie


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

async def download_file(request):
    session = request.app["session"]
    cookies = request.cookies
    project_id = request.match_info["project_id"]
    project = get_project_id(session, project_id)
    user_id = get_user_cookies(cookies)
    if user_id in (project.student_id, project.cogs_marker_id, project.supervisor_id) or \
            get_permission_from_cookie(cookies, "view_all_submitted_projects"):
        user_path = os.path.join("upload", str(project.student_id))
        if os.path.exists(user_path):
            filename = os.path.join(user_path, f"{project.group.series}_{project.group.part}.*")
            existing_files = glob.glob(filename)
            assert len(existing_files) <= 1
            if existing_files:
                filename = existing_files[0]
                return web.FileResponse(filename)
        return web.Response(status=404, text="Not found")
    return web.Response(status=403, text="Not authorised")
