from aiohttp.web import Request, Response
from ._format import JSONResonse, match_info_to_id


async def get_all(request: Request) -> Response:
    """
    Get information about currently existing rotations

    :param request:
    :return:
    """
    db = request.app["db"]
    rotations = {year: f"/api/series/{year}" for year in db.get_all_years()}
    return JSONResonse(links=rotations)


async def get(request: Request) -> Response:
    """
    Get information about currently existing rotations

    :param request:
    :return:
    """
    db = request.app["db"]
    year = match_info_to_id(request, "group_series")

    rotations = {rotation.part: f"/api/series/{year}/{rotation.part}"
                 for rotation in db.get_project_groups_by_series(year)}
    return JSONResonse(links=rotations)

