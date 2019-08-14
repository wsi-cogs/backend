from aiohttp.web import Request, Response
from typing import List, Dict, Optional
from zipfile import ZipFile, BadZipFile

from ._format import JSONResonse, HTTPError, get_match_info_or_error, get_params
from cogs.db.models import Project, ProjectGrade
from cogs.mail import sanitise
from cogs.scheduler.constants import SUBMISSION_GRACE_TIME, SUBMISSION_GRACE_TIME_PART_2
from cogs.security.middleware import permit


def serialise_project_to_json(project, include_mark_ids=False):
    return {
        "links": {
            "group": f"/api/series/{project.group.series}/{project.group.part}",
            "student": f"/api/users/{project.student_id}" if project.student_id is not None else None,
            "supervisor": f"/api/users/{project.supervisor_id}",
            "cogs_marker": f"/api/users/{project.cogs_marker_id}" if project.cogs_marker_id is not None else None
        },
        "data": project.serialise(include_mark_ids)
    }


def serialise_project(project, status=200, include_mark_ids=False):
    return JSONResonse(status=status,
                       **serialise_project_to_json(project, include_mark_ids))


async def get(request: Request) -> Response:
    """
    Get information about a project
    """
    db = request.app["db"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    user = request["user"]
    if not user.can_view_group(project.group):
        raise HTTPError(status=403,
                        message="Cannot view rotation")

    return serialise_project(
        project,
        include_mark_ids=user in {project.supervisor, project.cogs_marker, project.student} or user.role.view_all_submitted_projects
    )


@permit("create_projects")
async def create(request: Request) -> Response:
    """
    Create a new project
    """
    db = request.app["db"]
    user = request["user"]
    group = db.get_most_recent_group()

    if group.read_only:
        raise HTTPError(status=403,
                        message="No longer allowed to create projects for this group")

    project_data = await get_params(request, {
        "title": str,
        "authors": str,
        "wetlab": bool,
        "computational": bool,
        "abstract": str,
        "programmes": List[str],
        "student": Optional[int],
    })

    student_id = project_data.student
    if student_id is not None:
        student = db.get_user_by_id(student_id)
        student_project = db.get_projects_by_student(student, group)
        if student_project is not None:
            raise HTTPError(
                status=400,
                message="Student is already assigned to another project",
            )
    else:
        student = None

    project = Project(
        title=project_data.title,
        small_info=project_data.authors,
        is_wetlab=project_data.wetlab,
        is_computational=project_data.computational,
        abstract=sanitise(project_data.abstract),
        programmes="|".join(project_data.programmes),
        group_id=group.id,
        supervisor_id=user.id,
        student_id=student_id,
    )

    db.add(project)

    if student is not None:
        # Get all the student's choices, removing empty choices.
        choices: List[Optional[Project]] = list(filter(None, [student.first_option, student.second_option, student.third_option]))
        if project in choices:
            choices.remove(project)
        student.first_option = project
        # If the student has made no choices, `choices` will be empty,
        # so the padding on the end will be used instead.
        student.second_option, student.third_option, *_ = choices + [None]*3

    db.commit()

    return serialise_project(project, status=201, include_mark_ids=True)


@permit("create_projects")
async def edit(request: Request) -> Response:
    """
    Edit an existing project
    """
    db = request.app["db"]
    user = request["user"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)
    group = project.group

    if user != project.supervisor:
        raise HTTPError(status=403,
                        message="You don't own this project")

    project_data = await get_params(request, {
        "title": str,
        "authors": str,
        "wetlab": bool,
        "computational": bool,
        "abstract": str,
        "programmes": List[str],
        "student": Optional[int],
    })

    student_id = project_data.student
    if student_id != project.student_id and group.read_only:
        raise HTTPError(
            status=403,
            message="Cannot reassign students once projects are finalised",
        )
    if student_id is not None:
        student = db.get_user_by_id(student_id)
        student_project = db.get_projects_by_student(student, group)
        if student_project is not None and project != student_project:
            raise HTTPError(
                status=403,
                message="Student is already assigned to another project",
            )
    else:
        student = None

    project.title = project_data.title
    project.small_info = project_data.authors
    project.is_wetlab = project_data.wetlab
    project.is_computational = project_data.computational
    project.abstract = sanitise(project_data.abstract)
    project.programmes = "|".join(project_data.programmes)
    project.student_id = student_id

    if student is not None:
        # Get all the student's choices, removing empty choices.
        choices: List[Optional[Project]] = list(filter(None, [student.first_option, student.second_option, student.third_option]))
        if project in choices:
            choices.remove(project)
        student.first_option = project
        # If the student has made no choices, `choices` will be empty,
        # so the padding on the end will be used instead.
        student.second_option, student.third_option, *_ = choices + [None]*3

    db.commit()
    return serialise_project(project, include_mark_ids=True)


@permit("create_projects")
async def delete(request: Request) -> Response:
    """
    Delete a project
    """
    db = request.app["db"]
    user = request["user"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if user != project.supervisor or project.group.read_only:
        raise HTTPError(status=403,
                        message="You don't own this project or the project's group is read only")

    db.session.delete(project)
    db.commit()
    return JSONResonse(status=204)


async def mark(request: Request) -> Response:
    """
    Mark a project
    """
    db = request.app["db"]
    user = request["user"]
    mail = request.app["mailer"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if user not in (project.supervisor, project.cogs_marker):
        raise HTTPError(status=403,
                        message="You aren't assigned to mark this project")

    if project.grace_passed is not True:
        raise HTTPError(status=403,
                        message="This project hasn't been uploaded yet")

    if (user == project.supervisor and project.supervisor_feedback) or \
            (user == project.cogs_marker and project.cogs_feedback):
        raise HTTPError(status=403,
                        message="You have already marked this project")

    grade_data = await get_params(request, {"grade_id": int,
                                          "good_feedback": str,
                                          "general_feedback": str,
                                          "bad_feedback": str})

    grade = ProjectGrade(grade_id=grade_data.grade_id,
                         good_feedback=sanitise(grade_data.good_feedback),
                         bad_feedback=sanitise(grade_data.bad_feedback),
                         general_feedback=sanitise(grade_data.general_feedback))

    db.add(grade)
    db.session.flush()

    if user == project.supervisor:
        project.supervisor_feedback_id = grade.id
    if user == project.cogs_marker:
        project.cogs_feedback_id = grade.id

    db.commit()

    marker = user
    mail.send(project.student, "feedback_given", project=project, grade=grade, marker=marker)
    for user in db.get_users_by_permission("create_project_groups"):
        mail.send(user, "feedback_given", project=project, grade=grade, marker=marker)

    return serialise_project(project, include_mark_ids=True)


async def get_marks(request: Request) -> Response:
    """
    Get the marks for a project from both users
    """
    db = request.app["db"]
    user = request["user"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if user not in (project.supervisor, project.cogs_marker, project.student) and not user.role.view_all_submitted_projects:
        raise HTTPError(status=403,
                        message="You can't view the marks for this project")

    return JSONResonse(data={"cogs": project.cogs_feedback_id and project.cogs_feedback.serialise(),
                             "supervisor": project.supervisor_feedback_id and project.supervisor_feedback.serialise()})


@permit("view_all_submitted_projects", "modify_permissions")
async def set_cogs(request: Request) -> Response:
    """
    Apply new CoGS markers to a group of projects
    """
    db = request.app["db"]

    project_data = await get_params(request, {"projects": Dict[str, Optional[int]]})

    for project_id, cogs_member_id in project_data.projects.items():
        project = db.get_project_by_id(int(project_id))
        project.cogs_marker_id = cogs_member_id

    db.commit()

    return JSONResonse(links={},
                       data={})


async def upload(request: Request) -> Response:
    """
    Upload a project
    """
    db = request.app["db"]
    file_handler = request.app["file_handler"]
    mail = request.app["mailer"]
    scheduler = request.app["scheduler"]
    user = request["user"]

    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if user != project.student:
        return JSONResonse(
            status=403,
            status_message="Not authorised to upload project",
        )
    if project.grace_passed:
        return JSONResonse(
            status=403,
            status_message="Grace time exceeded"
        )

    current_size = 0
    max_size = file_handler.get_max_filesize()
    with file_handler.get_project(project, mode="wb") as project_file:
        reader = await request.multipart()
        while True:
            part = await reader.next()
            if part is None:
                break
            data = await part.read()
            current_size += len(data)
            if current_size > max_size:
                return JSONResonse(status=400,
                                   status_message="File too large. (Previous file possibly partially overwritten)")
            project_file.write(data)

    if not project.uploaded:
        project.uploaded = True
        project.grace_passed = False

        # Schedule grace period
        if project.group.part == 2:
            grace_time = project.group.student_complete + SUBMISSION_GRACE_TIME_PART_2
        else:
            grace_time = project.group.student_complete + SUBMISSION_GRACE_TIME

        scheduler.schedule_user_deadline(grace_time,
                                         "grace_deadline",
                                         f"project={project.id}",
                                         project_id=project.id)
        # Email grad office if no CoGS marker
        if project.cogs_marker is None:
            for grad_office_user in db.get_users_by_permission("create_project_groups"):
                mail.send(grad_office_user,
                          "cogs_not_found",
                          project=project)
    db.commit()

    return JSONResonse(status=204)


async def download(request: Request) -> Response:
    """
    Download a project
    """

    db = request.app["db"]
    user = request["user"]
    file_handler = request.app["file_handler"]

    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if not project.uploaded:
        return JSONResonse(
            status=404,
            status_message="Project not yet uploaded"
        )

    if user in (project.student, project.cogs_marker, project.supervisor) or user.role.view_all_submitted_projects:
        save_name = f"{project.student.name}_{project.group.series}_{project.group.part}.zip"
        try:
            with file_handler.get_project(project, "rb") as project_file:
                return Response(status=200,
                                headers={"Content-Disposition": f'inline; filename="{save_name}"',
                                         "Content-Type": "application/zip"},
                                body=project_file.read())
        except FileNotFoundError:
            return JSONResonse(
                status=500,
                status_message="Project not found on server - internal error"
            )
    return JSONResonse(
        status=403,
        status_message="Not authorised to download project"
    )


async def upload_information(request: Request) -> Response:
    """
    Get information about a project such as it's grace period and filenames.
    """
    db = request.app["db"]
    scheduler = request.app["scheduler"]
    file_handler = request.app["file_handler"]

    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if not project.uploaded:
        return JSONResonse(
            status=404,
            status_message="Project not yet uploaded"
        )

    job = scheduler.get_job(f"grace_deadline_{project.id}")
    grace_time = None
    if job:
        grace_time = job.next_run_time.strftime('%Y-%m-%d %H:%M')

    with file_handler.get_project(project, "rb") as project_file:
        try:
            with ZipFile(project_file) as project_zip:
                file_names = project_zip.namelist()
        except BadZipFile:
            file_names = []

    return JSONResonse(data={
        "grace_time": grace_time,
        "file_names": file_names
    })
