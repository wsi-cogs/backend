from aiohttp.web import Request, Response, HTTPTemporaryRedirect
from datetime import datetime, date

from ._format import JSONResonse, get_match_info_or_error, match_info_to_id, get_post, HTTPError
from cogs.scheduler.constants import GROUP_DEADLINES
from cogs.db.models import ProjectGroup


async def get_all(request: Request) -> Response:
    """
    Get information about currently existing rotations

    :param request:
    :return:
    """
    db = request.app["db"]
    rotations = {f"{rotation.series}-{rotation.part}": f"/api/series/{rotation.series}/{rotation.part}"
                 for rotation in db.get_all_series()}
    return JSONResonse(links=rotations)


async def get(request: Request) -> Response:
    """
    Get specific information a rotation

    :param request:
    :return:
    """
    db = request.app["db"]

    rotation = get_match_info_or_error(request, ["group_series", "group_part"], db.get_project_group)
    year = match_info_to_id(request, "group_series")

    return JSONResonse(links={"parent": f"/api/series/{year}",
                              "projects": [f"/api/projects/{project.id}" for project in rotation.projects]},
                       data=rotation.serialise())


async def latest(request: Request) -> JSONResonse:
    """
    Redirect to the latest rotation

    :param request:
    :return:
    """
    db = request.app["db"]
    latest = db.get_most_recent_group()
    return HTTPTemporaryRedirect(f"/api/series/{latest.series}/{latest.part}",
                                 headers={"Access-Control-Allow-Origin": "*"})


async def create(request: Request) -> JSONResonse:
    """
    Create a new rotation

    :param request:
    :return:
    """
    db = request.app["db"]

    rotation_data = await get_post(request, {"supervisor_submit": str,
                                             "student_invite": str,
                                             "student_choice": str,
                                             "student_complete": str,
                                             "marking_complete": str,
                                             "series": int,
                                             "part": int})

    try:
        deadlines = {deadline: datetime.strptime(getattr(rotation_data, deadline), "%Y-%m-%d")
                     for deadline in GROUP_DEADLINES}
    except ValueError:
        raise HTTPError(status=400,
                        message="Not all deadlines follow YYYY-MM-DD format")

    new_group = ProjectGroup(series=rotation_data.series,
                             part=rotation_data.part,
                             student_viewable=False,
                             student_choosable=False,
                             student_uploadable=False,
                             can_finalise=False,
                             read_only=False,
                             **deadlines)

    db.add(new_group)
    db.commit()

    return JSONResonse(status=201)


async def edit(request: Request) -> JSONResonse:
    """
    Create a new rotation

    :param request:
    :return:
    """
    db = request.app["db"]
    mail = request.app["mailer"]
    scheduler = request.app["scheduler"]

    rotation = get_match_info_or_error(request, ["group_series", "group_part"], db.get_project_group)

    rotation_data = await get_post(request, {"supervisor_submit": str,
                                             "student_invite": str,
                                             "student_choice": str,
                                             "student_complete": str,
                                             "marking_complete": str})

    try:
        deadlines = {deadline: datetime.strptime(getattr(rotation_data, deadline), "%Y-%m-%d")
                     for deadline in GROUP_DEADLINES}
    except ValueError:
        raise HTTPError(status=400,
                        message="Not all deadlines follow YYYY-MM-DD format")

    if deadlines["supervisor_submit"].date() != rotation.supervisor_submit:
        for supervisor in db.get_users_by_permission("create_projects"):
            mail.send(supervisor,
                      f"supervisor_invite_{group.part}",
                      new_deadline=deadlines["supervisor_submit"],
                      extension=True)

    for deadline in deadlines:
        if deadlines[deadline].date() != getattr(rotation, deadline):
            scheduler.schedule_deadline(deadlines[deadline], deadline, rotation)

        setattr(rotation, deadline, deadlines[deadline])

    db.commit()

    return JSONResonse(status=204)
