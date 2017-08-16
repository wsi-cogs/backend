import glob
import os
from datetime import datetime, timedelta

import aiofiles
from aiohttp import web
from aiohttp_jinja2 import template

from db_helper import get_user_cookies, get_most_recent_group, get_project_id
from permissions import view_only, get_permission_from_cookie
from scheduling.grace_deadline import add_grace_deadline


@template('student_upload.jinja2')
async def student_upload(request):
    session = request.app["session"]
    cookies = request.cookies
    group = get_most_recent_group(session)
    project = [project for project in group.projects if project.student_id == get_user_cookies(cookies)][0]
    if project.grace_passed:
        return web.Response(status=403, text="Grace time exceeded")
    scheduler = request.app["scheduler"]
    job = scheduler.get_job(f"grace_deadline_{project.id}")
    project_grace = None
    if job:
        project_grace = job.next_run_time.strftime('%Y-%m-%d %H:%M')
    return {"project": project,
            "grace_time": request.app["misc_config"]["submission_grace_time"],
            "project_grace": project_grace}


@view_only("join_projects")
async def on_submit(request):
    session = request.app["session"]
    group = get_most_recent_group(session)
    cookies = request.cookies
    user_id = get_user_cookies(cookies)
    project = [project for project in group.projects if project.student_id == user_id][0]
    if project.uploaded is None:
        add_grace_deadline(request.app["scheduler"],
                           project.id,
                           datetime.now() + timedelta(days=request.app["misc_config"]["submission_grace_time"]))
        project.uploaded = True
        project.grace_passed = False
    elif project.grace_passed:
        return web.json_response({"error": "Grace time exceeded"})
    post = await request.post()
    uploaded = post["qqfile"]
    extension = uploaded.filename.rsplit(".", 1)[1][:4]
    user_path = os.path.join("upload", str(user_id))
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    filename = os.path.join(user_path, f"{group.series}_{group.part}.")
    existing_files = glob.glob(filename+"*")
    if existing_files:
        for path in existing_files:
            os.remove(path)
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
