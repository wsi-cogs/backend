from aiohttp.web import Request, Response, HTTPTemporaryRedirect
from datetime import datetime

from ._format import JSONResonse, get_match_info_or_error, match_info_to_id, get_params, HTTPError
from cogs.scheduler.constants import GROUP_DEADLINES
from cogs.db.models import ProjectGroup
from typing import Dict

from cogs.security.middleware import permit


async def get_all(request: Request) -> Response:
    """
    Get information about currently existing rotations
    """
    db = request.app["db"]
    rotations = {f"{rotation.series}-{rotation.part}": f"/api/series/{rotation.series}/{rotation.part}"
                 for rotation in db.get_all_series()}
    return JSONResonse(links=rotations)


async def get(request: Request) -> Response:
    """
    Get specific information a rotation
    """
    db = request.app["db"]

    rotation = get_match_info_or_error(request, ["group_series", "group_part"], db.get_project_group)
    year = match_info_to_id(request, "group_series")

    user = request["user"]
    if not user.can_view_group(rotation):
        raise HTTPError(status=403,
                        message="Cannot view rotation")

    return JSONResonse(links={"parent": f"/api/series/{year}",
                              "projects": [f"/api/projects/{project.id}" for project in rotation.projects]},
                       data=rotation.serialise())


async def latest(request: Request) -> JSONResonse:
    """
    Redirect to the latest rotation
    """
    db = request.app["db"]
    latest = db.get_most_recent_group()
    return HTTPTemporaryRedirect(f"/api/series/{latest.series}/{latest.part}")


@permit("create_project_groups")
async def create(request: Request) -> JSONResonse:
    """
    Create a new rotation
    """
    db = request.app["db"]
    mail = request.app["mailer"]
    scheduler = request.app["scheduler"]

    rotation_data = await get_params(request, {
        "supervisor_submit": str,
        "student_invite": str,
        "student_choice": str,
        "student_complete": str,
        "marking_complete": str,
        "series": int,
        "part": int
    })

    try:
        deadlines = {deadline: datetime.strptime(getattr(rotation_data, deadline), "%Y-%m-%d")
                     for deadline in GROUP_DEADLINES}
    except ValueError:
        raise HTTPError(status=400,
                        message="Not all deadlines follow YYYY-MM-DD format")

    old_group = db.get_project_group(rotation_data.series, rotation_data.part)
    if old_group:
        raise HTTPError(status=400,
                        message="Cannot create a rotation with the same series and part as an existing rotation")

    rotation = ProjectGroup(
        series=rotation_data.series,
        part=rotation_data.part,
        student_viewable=False,
        student_choosable=False,
        student_uploadable=False,
        can_finalise=False,
        read_only=False,
        manual_supervisor_reminders=None,
        **deadlines
    )

    db.add(rotation)
    db.commit()

    for supervisor in db.get_users_by_permission("create_projects"):
        mail.send(
            supervisor,
            f"supervisor_invite_{rotation.part}",
            rotation=rotation,
        )

    for deadline in deadlines:
        scheduler.schedule_deadline(deadlines[deadline], deadline, rotation)

    return JSONResonse(status=201)


@permit("create_project_groups")
async def edit(request: Request) -> JSONResonse:
    """
    Edit an existing rotation
    """
    db = request.app["db"]
    mail = request.app["mailer"]
    scheduler = request.app["scheduler"]

    rotation = get_match_info_or_error(request, ["group_series", "group_part"], db.get_project_group)

    rotation_data = await get_params(request, {"deadlines": Dict[str, str], "attrs": Dict[str, bool]})
    try:
        deadlines = {deadline: datetime.strptime(rotation_data.deadlines[deadline], "%Y-%m-%d")
                     for deadline in GROUP_DEADLINES}
    except ValueError:
        raise HTTPError(status=400,
                        message="Not all deadlines follow YYYY-MM-DD format")

    old_deadline = rotation.supervisor_submit

    for deadline in deadlines:
        if deadlines[deadline].date() != getattr(rotation, deadline):
            scheduler.schedule_deadline(deadlines[deadline], deadline, rotation)
        setattr(rotation, deadline, deadlines[deadline])

    if deadlines["supervisor_submit"].date() != old_deadline:
        for supervisor in db.get_users_by_permission("create_projects"):
            mail.send(
                supervisor,
                f"supervisor_invite_{rotation.part}",
                rotation=rotation,
                old_deadline=old_deadline,
            )

    for attr, value in rotation_data.attrs.items():
        setattr(rotation, attr, value)

    db.commit()

    return JSONResonse(links={"parent": f"/api/series/{rotation.series}",
                              "projects": [f"/api/projects/{project.id}" for project in rotation.projects]},
                       data=rotation.serialise())


@permit("create_project_groups")
async def remind(request: Request) -> JSONResonse:
    """
    Send supervisors an email reminding them to submit a project
    """
    db = request.app["db"]
    mail = request.app["mailer"]

    rotation = get_match_info_or_error(request, ["group_series", "group_part"], db.get_project_group)
    rotation.manual_supervisor_reminders = datetime.now().date()
    db.commit()

    for supervisor in db.get_users_by_permission("create_projects"):
        mail.send(
            supervisor,
            f"supervisor_invite_{rotation.part}",
            rotation=rotation,
            reminder=True,
        )

    return JSONResonse(links={"parent": f"/api/series/{rotation.series}",
                              "projects": [f"/api/projects/{project.id}" for project in rotation.projects]},
                       data=rotation.serialise())
