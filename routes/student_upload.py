import glob
import os
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict
from zipfile import ZipFile, ZIP_DEFLATED

import aiofiles
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

import scheduling.deadlines
from db import Project
from db_helper import get_user_cookies, get_most_recent_group, get_project_id, get_student_project_group, \
    get_navbar_data
from mail import send_user_email
from permissions import view_only, get_permission_from_cookie, get_users_with_permission


@template('student_upload.jinja2')
@view_only("join_projects")
async def student_upload(request: Request) -> Dict:
    session = request.app["session"]
    cookies = request.cookies
    group = get_most_recent_group(session)
    project = get_student_project_group(session, get_user_cookies(request.app, cookies), group)
    if project.grace_passed:
        return web.Response(status=403, text="Grace time exceeded")
    scheduler = request.app["scheduler"]
    job = scheduler.get_job(f"grace_deadline_{project.id}")
    project_grace = None
    if job:
        project_grace = job.next_run_time.strftime('%Y-%m-%d %H:%M')
    return {"project": project,
            "grace_time": request.app["misc_config"]["submission_grace_time"],
            "project_grace": project_grace,
            "cur_option": "upload_project",
            **get_navbar_data(request)
            }


@view_only("join_projects")
async def on_submit(request: Request) -> Response:
    project_name = request.headers["name"]
    session = request.app["session"]
    group = get_most_recent_group(session)
    cookies = request.cookies
    user_id = get_user_cookies(request.app, cookies)

    max_files_for_project = 1
    if group.part == 2:
        max_files_for_project = 2

    # Send out email if required
    project = next(project for project in group.projects if project.student_id == user_id)
    if project.grace_passed:
        return web.json_response({"error": "Grace time exceeded"})

    # Setup for downloading
    reader = await request.multipart()
    await reader.next()
    # aiohttp does weird stuff and doesn't set content headers correctly so we've got to do it manually
    uploader = await reader.next()
    filename = await uploader.read()
    extension = filename.rsplit(b".", 1)[1][:4].decode("ascii")
    user_path = os.path.join("upload", str(user_id))
    if not os.path.exists("upload"):
        os.mkdir("upload")
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    filename = os.path.join(user_path, f"{group.series}_{group.part}")
    existing_files = glob.glob(filename+"*")
    if len(existing_files) >= max_files_for_project:
        for path in existing_files:
            os.remove(path)
        existing_files = []
    # Download the actual file
    await reader.next()
    uploader = await reader.next()
    async with aiofiles.open(f"{filename}_{len(existing_files)+1}.{extension}", mode="wb") as f:
        while True:
            chunk = await uploader.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            await f.write(chunk)
    if not project.uploaded and len(existing_files) + 1 == max_files_for_project:
        if project.group.part == 2:
            # Rotation 2 should be editable until the deadline
            grace_time = project.group.student_complete + timedelta(days=1)
        else:
            grace_time = datetime.now() + timedelta(days=request.app["misc_config"]["submission_grace_time"])

        scheduling.deadlines.add_grace_deadline(request.app["scheduler"],
                                                project.id,
                                                grace_time)
        project.uploaded = True
        project.grace_passed = False
        if project.cogs_marker is None:
            for grad_office_user in get_users_with_permission(request.app, "create_project_groups"):
                await send_user_email(request.app,
                                      grad_office_user,
                                      "cogs_not_found",
                                      project=project)
    project.title = project_name
    session.commit()
    return web.json_response({"success": True})


async def download_file(request: Request) -> Response:
    session = request.app["session"]
    cookies = request.cookies
    project_id = int(request.match_info["project_id"])
    project = get_project_id(session, project_id)
    user_id = get_user_cookies(request.app, cookies)
    if user_id in (project.student_id, project.cogs_marker_id, project.supervisor_id) or \
            get_permission_from_cookie(request.app, cookies, "view_all_submitted_projects"):
        save_name = f"{project.student.name}_{project.group.series}_{project.group.part}"
        paths = get_stored_paths(project)
        file = BytesIO()
        with ZipFile(file, 'w', ZIP_DEFLATED) as zip_f:
            for i, path in enumerate(paths):
                extension = path.rsplit(".", 1)[1]
                zip_f.write(path,
                            arcname=f"{save_name}_{i+1}.{extension}")
        file.seek(0)
        return web.Response(status=200,
                            headers={"Content-Disposition": f'inline; filename="{save_name}.zip"'},
                            body=file.read())
    return web.Response(status=403, text="Not authorised")


def get_stored_paths(project: Project) -> List[str]:
    user_path = os.path.join("upload", str(project.student_id))
    if os.path.exists(user_path):
        filename = os.path.join(user_path, f"{project.group.series}_{project.group.part}*")
        existing_files = glob.glob(filename)
        assert len(existing_files) >= 1
        return existing_files
