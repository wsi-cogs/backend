from typing import List, Dict, Union, Optional

from aiohttp.web import Request, Response, HTTPTemporaryRedirect

from ._format import JSONResonse, get_match_info_or_error, get_params, HTTPError
from .projects import serialise_project_to_json
from cogs.db.models import User, Project
from cogs.common.constants import JOB_HAZARD_FORM
from cogs.security.middleware import permit


def serialise_user_to_json(db, user):
    supervising_projects = db.get_projects_by_supervisor(user)
    cogs_projects = db.get_projects_by_cogs_marker(user)
    student_projects = db.get_projects_by_student(user)
    can_upload_project = False
    current_student_project = None
    if student_projects:
        most_recent = student_projects[-1]
        can_upload_project = bool(most_recent.group.student_uploadable and not most_recent.grace_passed)
        current_student_project = most_recent.id

    return {
        "links": {
            "parent": "/api/users",
            "choice_1": f"/api/projects/{user.first_option_id}" if user.first_option_id is not None else None,
            "choice_2": f"/api/projects/{user.second_option_id}" if user.second_option_id is not None else None,
            "choice_3": f"/api/projects/{user.third_option_id}" if user.third_option_id is not None else None,
            "supervisor_projects": [f"/api/projects/{project.id}" for project in supervising_projects],
            "cogs_projects": [f"/api/projects/{project.id}" for project in cogs_projects],
            "student_projects": [f"/api/projects/{project.id}" for project in student_projects]
        },
        "data": {
            "can_upload_project": can_upload_project,
            "current_student_project": current_student_project,
            **user.serialise()
        }
    }


async def me(request: Request) -> Response:
    """
    Get information about the current logged in user
    """
    user_id = request["user"].id
    return HTTPTemporaryRedirect(f"/api/users/{user_id}")


async def get_all(request: Request) -> Response:
    """
    Get information about users
    """
    db = request.app["db"]
    users = {user.id: f"/api/users/{user.id}" for user in db.get_all_users()}
    return JSONResonse(links=users)


async def get_with_permission(request: Request) -> Response:
    """
    Get information about users with any of a list of permissions
    """
    db = request.app["db"]
    permissions = await get_params(request, {"permissions": List[str]})
    users = {user.id: f"/api/users/{user.id}" for user in db.get_users_by_permission(*set(permissions.permissions))}
    return JSONResonse(links=users)


async def get(request: Request) -> Response:
    """
    Get information about a specific user
    """
    db = request.app["db"]
    user = get_match_info_or_error(request, "user_id", db.get_user_by_id)

    return JSONResonse(**serialise_user_to_json(db, user))


@permit("modify_permissions")
async def edit(request: Request) -> Response:
    """
    Modify a user
    """
    db = request.app["db"]
    user = get_match_info_or_error(request, "user_id", db.get_user_by_id)

    user_data = await get_params(request, {"name": str,
                                         "email": Optional[str],
                                         "email_personal": Optional[str],
                                         "user_type": List[str],
                                         "priority": int})
    if user == request["user"] and \
            "grad_office" in request["user"].user_type.split("|") and \
            "grad_office" not in user_data.user_type:
        raise HTTPError(
            status=400,
            message="Cannot remove the grad office role from yourself"
        )
    user.name = user_data.name
    user.email = user_data.email
    user.email_personal = user_data.email_personal
    user.user_type = "|".join(user_data.user_type)
    user.priority = min(100, max(0, user_data.priority))

    db.commit()
    return JSONResonse(**serialise_user_to_json(db, user))


@permit("modify_permissions")
async def create(request: Request) -> Response:
    """
    Create a new user
    """
    db = request.app["db"]
    user_data = await get_params(request, {"name": str,
                                         "email": str,
                                         "email_personal": str,
                                         "user_type": List[str],
                                         "priority": int})

    user = User(name=user_data.name,
                email=user_data.email,
                email_personal=user_data.email_personal,
                priority=min(100, max(0, user_data.priority)),
                user_type="|".join(user_data.user_type))

    db.add(user)
    db.commit()

    return JSONResonse(**serialise_user_to_json(db, user))


# User model attributes for project options
_ATTRS = ("first_option_id", "second_option_id", "third_option_id")


@permit("join_projects")
async def vote(request: Request) -> Response:
    """
    Vote on a project as your first, second or third choice
    """
    db = request.app["db"]
    user = request["user"]

    voting_data = await get_params(request, {"project_id": int, "choice": int})

    project = db.get_project_by_id(voting_data.project_id)
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


@permit("view_all_submitted_projects")
async def assign_projects(request: Request) -> Response:
    """
    Assign a list of students projects.
    Can be given users to auto-create projects for them.
    """
    db = request.app["db"]
    student_choices = await get_params(request, {"choices": Dict[str, Dict[str, Union[str, int]]]})
    group = db.get_most_recent_group()

    def get_project(project_id, student_id):
        return db.get_project_by_id(project_id), None

    def get_supervisor(supervisor_id, student_id):
        student = db.get_user_by_id(student_id)
        project = Project(
            title=f"Dummy project for {student.name}",
            small_info="",
            is_wetlab=False,
            is_computational=False,
            abstract="A dummy project created automatically. Please fill in the details for it once established.",
            programmes="",
            group_id=group.id,
            supervisor_id=supervisor_id
        )
        db.add(project)
        student.first_option = project
        return project, student

    choice_map = {
        "project": get_project,
        "user": get_supervisor
    }

    for project in group.projects:
        project.student_id = None

    projects = []
    students = []
    for student_id_str, choice in student_choices.choices.items():
        student_id = int(student_id_str)
        choice_type = choice["type"]
        choice_id = int(choice["id"])

        project, student = choice_map[choice_type](choice_id, student_id)
        project.student_id = student_id
        projects.append(project)
        if student:
            students.append(student)
    db.commit()

    serialised_projects = [serialise_project_to_json(project) for project in projects]
    serialised_users = [serialise_user_to_json(db, user) for user in students]
    return JSONResonse(status=200,
                       data={
                           "projects": serialised_projects,
                           "users": serialised_users
                       })


@permit("view_all_submitted_projects")
async def unset_votes(request: Request) -> Response:
    """
    Unset all student's votes and set priority correctly.
    Also send emails to supervisors and students as to their projects.
    """
    db = request.app["db"]
    mail = request.app["mailer"]

    group = db.get_most_recent_group()
    group.student_uploadable = True
    group.can_finalise = False
    group.student_choosable = False

    priorities = {}

    for project in filter(lambda p: p.student, group.projects):
        student = project.student
        project.student_uploadable = True

        try:
            choice = (student.first_option_id, student.second_option_id, student.third_option_id).index(project.id)
        except ValueError:
            choice = 3

        student.priority += (2 ** choice) - 1

        priorities[student.id] = student.priority
        student.first_option = None
        student.second_option = None
        student.third_option = None

        mail.send(student, "project_selected_student", project=project)

    for supervisor in db.get_users_by_permission("create_projects"):
        projects = db.get_projects_by_supervisor(supervisor, group)

        if projects:
            mail.send(supervisor, "project_selected_supervisor", JOB_HAZARD_FORM, projects=projects)
        mail.send(supervisor, "supervisor_student_project_list", projects=group.projects)

    db.commit()
    return JSONResonse(data={
        "priorities": priorities
    })
