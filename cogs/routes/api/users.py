from typing import List

from aiohttp.web import Request, Response, HTTPTemporaryRedirect

from ._format import JSONResonse, get_match_info_or_error, get_post, HTTPError
from cogs.db.models import User

async def get_all(request: Request) -> Response:
    """
    Get information about users

    :param request:
    :return:
    """
    db = request.app["db"]
    users = {user.id: f"/api/users/{user.id}" for user in db.get_all_users()}
    return JSONResonse(links=users)


async def get(request: Request) -> Response:
    """
    Get information about a specific user

    :param request:
    :return:
    """
    db = request.app["db"]
    user = get_match_info_or_error(request, "user_id", db.get_user_by_id)

    supervising_projects = db.get_projects_by_supervisor(user)
    cogs_projects = db.get_projects_by_cogs_marker(user)
    student_projects = db.get_projects_by_student(user)
    return JSONResonse(links={"parent": "/api/users",
                              "choice_1": f"/api/projects/{user.first_option_id}" if user.first_option_id is not None else None,
                              "choice_2": f"/api/projects/{user.second_option_id}" if user.second_option_id is not None else None,
                              "choice_3": f"/api/projects/{user.third_option_id}" if user.third_option_id is not None else None,
                              "supervisor_projects": [f"/api/projects/{project.id}" for project in supervising_projects],
                              "cogs_projects": [f"/api/projects/{project.id}" for project in cogs_projects],
                              "student_projects": [f"/api/projects/{project.id}" for project in student_projects]
                              },
                       data=user.serialise())


async def edit(request: Request) -> Response:
    """
    Modify a user

    :param request:
    :return:
    """
    db = request.app["db"]
    user = get_match_info_or_error(request, "user_id", db.get_user_by_id)

    user_data = await get_post(request, {"name": str,
                                         "email": str,
                                         "user_type": List[str],
                                         "priority": int})
    user.name = user_data.name
    user.email = user_data.email
    user.user_type = "|".join(user_data.user_type)
    user.priority = min(100, max(0, user_data.priority))

    db.commit()
    return JSONResonse(status=204)


async def create(request: Request) -> Response:
    """
    Create a new user

    :param request:
    :return:
    """
    db = request.app["db"]
    user_data = await get_post(request, {"name": str,
                                         "email": str,
                                         "user_type": List[str],
                                         "priority": int})

    user = User(name=user_data.name,
                email=user_data.email,
                priority=min(100, max(0, user_data.priority)),
                user_type="|".join(user_data.user_type))

    db.add(user)
    db.commit()

    return JSONResonse(data={"user_id": user.id})


async def me(request: Request) -> Response:
    """
    Get information about the current logged in user

    :param request:
    :return:
    """
    user_id = request["user"].id
    return HTTPTemporaryRedirect(f"/api/users/{user_id}")


# User model attributes for project options
_ATTRS = ("first_option_id", "second_option_id", "third_option_id")


async def vote(request: Request) -> Response:
    """
    Vote on a project as your first, second or third choice

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]

    voting_data = await get_post(request, {"project_id": int, "choice": int})

    project = db.get_project_by_id(voting_data.choice)
    if not db.can_student_choose_project(user, project):
        raise HTTPError(status=403,
                        message="You cannot choose this project")

    for i, attr in enumerate(_ATTRS):
        if i == voting_data.choice-1:
            # Set the choice they made
            setattr(user, attr, project.id)
        elif getattr(user, attr) == project.id:
            # If they already had that as a different priority, unset the old one
            setattr(user, attr, None)

    db.commit()
    return JSONResonse(status=204)
