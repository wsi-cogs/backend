from collections import defaultdict
from datetime import date
from typing import Optional, List, Union, Dict

from aiohttp.web import Application
from sqlalchemy import desc
import json

from db import ProjectGroup, Project, User, EmailTemplate
from permissions import is_user, get_user_permissions, can_view_group
from type_hints import DBSession, Cookies


def get_most_recent_group(session: DBSession) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup created most recently

    :param session:
    :return ProjectGroup:
    """
    return session.query(ProjectGroup).order_by(desc(ProjectGroup.id)).first()


def get_group(session: DBSession, series: int, part: int) -> Optional[ProjectGroup]:
    """
    Get the ProjectGroup with the corresponding series and part.

    :param session:
    :param series:
    :param part:
    :return ProjectGroup:
    """
    assert isinstance(series, int)
    assert isinstance(part, int)
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).filter(ProjectGroup.part == part).first()


def get_series(session: DBSession, series: int) -> List[ProjectGroup]:
    """
    Get all ProjectGroups associated the corresponding series.

    :param session:
    :param series:
    :return ProjectGroup:
    """
    assert isinstance(series, int)
    return session.query(ProjectGroup).filter(ProjectGroup.series == series).order_by(ProjectGroup.part).all()


def get_projects_supervisor(session: DBSession, user_id: int) -> List[List[Project]]:
    """
    Get all the projects that belong to a user.

    :param session:
    :param user_id:
    :return:
    """
    assert isinstance(user_id, int)
    projects = session.query(Project).filter_by(supervisor_id=user_id).all()
    read_only_map = {}
    rtn = {}
    for project in projects:
        if project.group_id not in read_only_map:
            read_only_map[project.group_id] = project.group.read_only
            rtn[project.group_id] = []
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def get_projects_cogs(app, cookies: Cookies) -> List[List[Project]]:
    """
    Get a list of projects the logged in user is the CoGS marker for

    :param app:
    :param cookies:
    :return:
    """
    user_id = get_user_cookies(app, cookies)
    projects = app["session"].query(Project).filter_by(cogs_marker_id=user_id).all()
    rtn = defaultdict(list)
    for project in projects:
        rtn[project.group_id].append(project)
    return [rtn[key] for key in sorted(rtn.keys(), reverse=True)]


def set_project_read_only(app, cookies: Cookies, project: Project):
    project.read_only = project.group.read_only or not is_user(app, cookies, project.supervisor)


def set_project_can_resubmit(app, cookies: Cookies, project: Project):
    most_recent = get_most_recent_group(app["session"])
    if project.group == most_recent:
        project.can_resubmit = False
    else:
        project.can_resubmit = project.group.read_only and is_user(app, cookies, project.supervisor)


def set_project_can_mark(app, cookies: Cookies, project: Project):
    project.can_mark = can_provide_feedback(app, cookies, project)


def get_project_name(session: DBSession, project_name: str) -> Optional[Project]:
    """
    Get a project by it's name.
    If there is already a project with this name, return the newest one.

    :param session:
    :param project_name:
    :return:
    """
    assert isinstance(project_name, str)
    return session.query(Project).filter_by(title=project_name).order_by(Project.id.desc()).first()


def get_project_id(session: DBSession, project_id: int) -> Optional[Project]:
    """
    Get a project by it's id.

    :param session:
    :param project_id:
    :return:
    """
    assert isinstance(project_id, int)
    return session.query(Project).filter_by(id=project_id).first()


def get_user_cookies(app, cookies: Cookies) -> int:
    """
    Get the user id of the current logged in user or -1

    :param app:
    :param cookies:
    :return:
    """
    if "login_session" not in app:
        return 1
    if "Pagesmith_User" not in cookies:
        return -1
    pagesmith_user = cookies["Pagesmith_User"]
    pagesmith_user = pagesmith_user.replace("%0A", "")  # He's got a bug in his perl.
    decrypted = app.blowfish.decrypt(pagesmith_user)
    perm, uuid, refresh, expiry, ip = decrypted.split(b" ")
    uuid = uuid.decode()
    # It weirdly doesn't update the transaction when you login so you've got to do it manually for some reason
    cur = app["login_session"].cursor()
    app["login_session"].commit()
    with cur:
        cur.execute("SELECT content FROM session WHERE type='User' AND session_key = %s;", (uuid,))
        data = cur.fetchone()
        if data is None:
            return -1
    data = data[0][1:].decode()
    decrypted_json = app.blowfish.decrypt(data)
    user_data = json.loads(decrypted_json)
    user = app["session"].query(User).filter_by(email=user_data["email"]).first()
    if not user:
        return -2
    return user.id


def get_user_id(app, cookies: Optional[Cookies] = None, user_id: Optional[int] = None) -> Optional[User]:
    """
    Get a user, either by the current logged in one or by user id

    :param app:
    :param cookies:
    :param user_id:
    :return:
    """
    assert not (cookies is None and user_id is None), "Must pass either cookies or user_id"
    if cookies is not None:
        user_id = get_user_cookies(app, cookies)
    assert isinstance(user_id, int)
    return app["session"].query(User).filter_by(id=user_id).first()


def get_all_users(session: DBSession) -> List[User]:
    """
    Get all users in the system

    :param session:
    :return:
    """
    return session.query(User).all()


def get_all_groups(session: DBSession) -> List[ProjectGroup]:
    """
    Get all rotations in the system

    :param session:
    :return:
    """
    return session.query(ProjectGroup).all()


def get_student_projects(app, cookies: Cookies) -> List[Project]:
    """
    Returns a list of projects the current logged in user is a student for

    :param app:
    :param cookies:
    :return:
    """
    user_id = get_user_cookies(app, cookies)
    projects = app["session"].query(Project).filter_by(student_id=user_id).all()
    return sort_by_attr(projects, "id")


def get_student_project_group(session: DBSession, user_id: int, group: ProjectGroup):
    """


    :param session:
    :param user_id:
    :param group:
    :return:
    """
    assert isinstance(user_id, int)
    project = session.query(Project).filter_by(student_id=user_id).filter_by(group_id=group.id).first()
    return project


def get_students_series(session: DBSession, series: int):
    assert isinstance(series, int)
    rotations = get_series(session, series)
    students = []
    for rotation in rotations:
        for project in rotation.projects:
            if project.student not in students:
                students.append(project.student)
    return students


def can_provide_feedback(app, cookies: Cookies, project: Project) -> bool:
    """
    Can a user provide feedback to a project?

    :param app:
    :param cookies:
    :param project:
    :return:
    """
    logged_in_user = get_user_cookies(app, cookies)
    if project.grace_passed:
        return should_pester_feedback(project, user_id=logged_in_user)
    return False


def should_pester_upload(app: Application, user: User) -> bool:
    """
    Should the system pester a supervisor to upload projects?
    It should if they haven't uploaded one for this group.

    :param app:
    :param user:
    :return:
    """
    group = get_most_recent_group(app["session"])
    for project in group.projects:
        if project.supervisor == user:
            return False
    return True


def should_pester_feedback(project: Project, user_id: int) -> bool:
    """
    Should the system pester a user to provide feedback on a project?
    It should if they haven't yet done so.

    :param project:
    :param user_id:
    :return:
    """
    if user_id == project.supervisor.id:
        return project.supervisor_feedback_id is None
    elif user_id == project.cogs_marker.id:
        return project.cogs_feedback_id is None
    return False


def set_group_attributes(app, cookies: Cookies, group: Union[ProjectGroup, List[Project]]) -> List[Project]:
    """
    Return a list of all the projects in a ProjectGroup

    :param app:
    :param cookies:
    :param group:
    :return:
    """
    try:
        projects = group.projects
    except AttributeError:
        projects = group
    for project in projects:
        set_project_can_mark(app, cookies, project)
        set_project_can_resubmit(app, cookies, project)
        set_project_read_only(app, cookies, project)
    return sort_by_attr(projects, "can_mark")


def sort_by_attr(projects: List[Project], attr: str) -> List[Project]:
    """
    Sort a list of projects by an attribute of a project.

    :param projects:
    :param attr:
    :return:
    """
    projects.sort(key=lambda project: getattr(project, attr), reverse=True)
    return projects


def get_dates_from_group(group: ProjectGroup) -> Dict:
    rtn = {}
    for column in group.__table__.columns:
        rtn[column.key] = getattr(group, column.key)
        if isinstance(rtn[column.key], date):
            rtn[column.key] = rtn[column.key].strftime("%d/%m/%Y")
    return rtn


def get_navbar_data(request):
    session = request.app["session"]
    most_recent = get_most_recent_group(session)
    user = get_user_id(request.app, request.cookies)
    permissions = get_user_permissions(request.app, user)
    root_map = {"join_projects": "My Choices",
                "create_projects": "My Owned Projects",
                "create_project_groups": "Rotations"}
    rtn = {
        "can_edit": not most_recent.read_only,
        "deadlines": request.app["deadlines"],
        "display_projects_link": can_view_group(request, most_recent),
        "user": user,
        "show_login_bar": "login_session" not in request.app,
        "root_title": ", ".join(root_map[perm] for perm in permissions if perm in root_map) or "Main Page"
    }
    if "view_all_submitted_projects" in permissions:
        series_groups = get_series(session, most_recent.series)
        rtn["series_years"] = sorted({group.series for group in get_all_groups(session)}, reverse=True)
        rtn["rotations"] = sorted((group.part for group in series_groups), reverse=True)
    rtn["show_submit"] = False
    if "join_projects" in permissions:
        project = get_student_project_group(session, user.id, most_recent)
        if project and project.group.student_uploadable and not project.grace_passed:
            rtn["show_submit"] = True
    if "create_project_groups" in permissions:
        rtn["groups"] = [get_dates_from_group(group) for group in series_groups]
        if most_recent.student_choice < date.today():
            rtn["show_create_rotation"] = True
    if "set_readonly" in permissions:
        rtn["show_finalise_choices"] = most_recent.can_finalise
    rtn["permissions"] = permissions
    return rtn


def get_templates(session: DBSession) -> List[EmailTemplate]:
    """
    Get all EmailTemplate associated the corresponding series.

    :param session:
    :return List[EmailTemplate]:
    """
    return session.query(EmailTemplate).order_by(EmailTemplate.name).all()


def get_template_name(session: DBSession, name: str) -> EmailTemplate:
    """
    Get all EmailTemplate associated the corresponding series.

    :param session:
    :param name:
    :return EmailTemplate:
    """
    return session.query(EmailTemplate).filter_by(name=name).first()
