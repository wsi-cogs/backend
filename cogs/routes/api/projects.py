from aiohttp.web import Request, Response
from ._format import JSONResonse, HTTPError, get_match_info_or_error, get_params
from typing import List, Dict, Optional
from cogs.db.models import Project, ProjectGrade
from cogs.mail import sanitise


def serialise_project_to_json(project):
    return {
        "links": {
            "group": f"/api/series/{project.group.series}/{project.group.part}",
            "student": f"/api/users/{project.student_id}" if project.student_id is not None else None,
            "supervisor": f"/api/users/{project.supervisor_id}",
            "cogs_marker": f"/api/users/{project.cogs_marker_id}" if project.cogs_marker_id is not None else None
        },
        "data": project.serialise()
    }


def serialise_project(project, status=200):
    return JSONResonse(status=status,
                       **serialise_project_to_json(project))


async def get(request: Request) -> Response:
    """
    Get information about a project

    :param request:
    :return:
    """
    db = request.app["db"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)
    return serialise_project(project)


async def create(request: Request) -> Response:
    """    Create a new project

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    group = db.get_most_recent_group()

    if group.read_only:
        raise HTTPError(status=403,
                        message="No longer allowed to create projects for this group")

    project_data = await get_params(request, {"title": str,
                                              "authors": str,
                                              "wetlab": bool,
                                              "computational": bool,
                                              "abstract": str,
                                              "programmes": List[str]})

    project = Project(title=project_data.title,
                      small_info=project_data.authors,
                      is_wetlab=project_data.wetlab,
                      is_computational=project_data.computational,
                      abstract=sanitise(project_data.abstract),
                      programmes="|".join(project_data.programmes),
                      group_id=group.id,
                      supervisor_id=user.id)

    db.add(project)
    db.commit()

    return serialise_project(project, status=201)


async def edit(request: Request) -> Response:
    """
    Create a new project

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if user != project.supervisor:
        raise HTTPError(status=403,
                        message="You don't own this project")

    project_data = await get_params(request, {"title": str,
                                            "authors": str,
                                            "wetlab": bool,
                                            "computational": bool,
                                            "abstract": str,
                                            "programmes": List[str]})

    project.title = project_data.title
    project.small_info = project_data.authors
    project.is_wetlab = project_data.wetlab
    project.is_computational = project_data.computational
    project.abstract = sanitise(project_data.abstract)
    project.programmes = "|".join(project_data.programmes)

    db.commit()
    return serialise_project(project)


async def delete(request: Request) -> Response:
    """
    Delete a project

    :param request:
    :return:
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

    :param request:
    :return:
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

    mail.send(project.student, "feedback_given", project=project, grade=grade, marker=user)
    for user in db.get_users_by_permission("create_project_groups"):
        mail.send(user, "feedback_given", project=project, grade=grade, marker=user)

    return serialise_project(project)


def get_marks(request: Request) -> Response:
    """
    Get the marks for a project from both users

    :param request:
    :return:
    """
    db = request.app["db"]
    user = request["user"]
    project = get_match_info_or_error(request, "project_id", db.get_project_by_id)

    if user not in (project.supervisor, project.cogs_marker) and not user.role.view_all_submitted_projects:
        raise HTTPError(status=403,
                        message="You can't view the marks for this project")

    return JSONResonse(data={"cogs": project.cogs_feedback_id and project.cogs_feedback.serialise(),
                             "supervisor": project.supervisor_feedback_id and project.supervisor_feedback.serialise()})


async def set_cogs(request: Request) -> Response:
    """
    Apply new CoGS markers to a group of projects

    :param request:
    :return:
    """
    db = request.app["db"]

    project_data = await get_params(request, {"projects": Dict[str, Optional[int]]})

    for project_id, cogs_member_id in project_data.projects.items():
        project = db.get_project_by_id(int(project_id))
        project.cogs_marker_id = cogs_member_id

    db.commit()

    return JSONResonse(links={},
                       data={})
