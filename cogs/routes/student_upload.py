"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
* Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from datetime import datetime
from io import BytesIO
from typing import Dict
from zipfile import ZipFile, ZIP_DEFLATED

from aiohttp import web
from aiohttp.web import Request, Response, HTTPForbidden
from aiohttp_jinja2 import template

from cogs.security.middleware import permit
from cogs.scheduler.constants import SUBMISSION_GRACE_TIME, SUBMISSION_GRACE_TIME_PART_2


@template('student_upload.jinja2')
@permit("join_projects")
async def student_upload(request: Request) -> Dict:
    db = request.app["db"]
    navbar_data = request["navbar"]
    scheduler = request.app["scheduler"]

    group = db.get_most_recent_group()
    project = db.get_projects_by_student(request["user"], group)
    if project.grace_passed:
        raise HTTPForbidden(text="Grace time exceeded")

    job = scheduler.get_job(f"grace_deadline_{project.id}")
    project_grace = None
    if job:
        project_grace = job.next_run_time.strftime('%Y-%m-%d %H:%M')

    pretty_delta = str(SUBMISSION_GRACE_TIME).replace(", 0:00:00", "", 1)
    return {"project": project,
            "grace_time": pretty_delta,
            "project_grace": project_grace,
            "cur_option": "upload_project",
            **navbar_data
            }


@permit("join_projects")
async def on_submit(request: Request) -> Response:
    project_name = request.headers["name"]
    db = request.app["db"]
    user = request["user"]
    mailer = request.app["mailer"]
    file_handler = request.app["file_handler"]
    scheduler = request.app["scheduler"]

    group = db.get_most_recent_group()
    project = db.get_projects_by_student(student=user, group=group)
    if project.grace_passed:
        return web.json_response({"error": "Grace time exceeded"})

    # Setup for downloading
    reader = await request.multipart()
    await reader.next()
    # aiohttp does weird stuff and doesn't set content headers correctly so we've got to do it manually
    uploader = await reader.next()

    # Get the filename and extension
    filename = await uploader.read()
    extension = filename.rsplit(b".", 1)[1].decode("ascii")

    # Download the actual file
    await reader.next()
    uploader = await reader.next()
    # Setup the file handle
    file_handle, set_grace = file_handler.upload_file(user, project, extension)
    with file_handle:
        while True:
            chunk = await uploader.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            file_handle.write(chunk)

    if not project.uploaded and set_grace:
        # Set up the grace period and send out emails if no cogs marker
        if project.group.part == 2:
            # Rotation 2 should be editable until the deadline
            grace_time = project.group.student_complete + SUBMISSION_GRACE_TIME_PART_2
        else:
            grace_time = datetime.now() + SUBMISSION_GRACE_TIME

        scheduler.schedule_user_deadline(grace_time,
                                         "grace_deadline",
                                         project.id,
                                         project.id)
        project.uploaded = True
        project.grace_passed = False
        if project.cogs_marker is None:
            for grad_office_user in db.get_users_by_permission("create_project_groups"):
                mailer.send(grad_office_user,
                            "cogs_not_found",
                            project=project)
    project.title = project_name
    db.commit()
    return web.json_response({"success": True})


async def download_file(request: Request) -> Response:
    db = request.app["db"]
    user = request["user"]
    file_handler = request.app["file_handler"]

    project_id = int(request.match_info["project_id"])
    project = db.get_project_by_id(project_id)

    if user in (project.student, project.cogs_marker, project.supervisor) or user.role.view_all_submitted_projects:
        save_name = f"{project.student.name}_{project.group.series}_{project.group.part}"
        paths = file_handler.get_files_by_project(project)
        file = BytesIO()
        with ZipFile(file, 'w', ZIP_DEFLATED) as zip_f:
            for i, path in enumerate(paths):
                extension = path.rsplit(".", 1)[1]
                zip_f.write(path,
                            arcname=f"{save_name}_{i+1}.{extension}")
        file.seek(0)
        return Response(status=200,
                        headers={"Content-Disposition": f'inline; filename="{save_name}.zip"',
                                 "Content-Type": "application/zip"},
                        body=file.read())
    return Response(status=403, text="Not authorised")
