from typing import Union, Collection, Callable, Set, Sequence

from aiohttp import web

import db_helper


def get_permission_from_cookie(cookies, permission: str) -> bool:
    """
    Given a cookie store, return if the user is allowed a given permission.

    :param cookies:
    :param permission:
    :return:
    """
    return cookies.get(permission, False) == "True"


def view_only(permissions: Union[Collection, str]):
    """
    Returns a 403 status error is the client is not authorised to view the content.
    Otherwise allows the function to be called as normal.

    :param permissions:
    :return:
    """
    def decorator(func):
        def inner(request):
            nonlocal permissions
            if isinstance(permissions, str):
                permissions = (permissions, )
            for permission in permissions:
                if not get_permission_from_cookie(request.cookies, permission):
                    return web.Response(status=403, text="Permission Denied")
            return func(request)
        return inner
    return decorator


def is_user(cookies, user) -> bool:
    """
    Return if the currently logged in user is the passed user

    :param cookies:
    :param user_id:
    :return:
    """
    return int(cookies.get("user_id", "-1")) == user.id


def can_view_group(request, group) -> bool:
    cookies = request.cookies
    if get_permission_from_cookie(cookies, "view_projects_predeadline"):
        return True
    return group.student_viewable


def can_choose_project(session, cookies, project) -> bool:
    if get_permission_from_cookie(cookies, "join_projects"):
        if project.group.student_choosable:
            if project.group.part != 3:
                return True
            done_projects = db_helper.get_student_projects(session, cookies)
            done_projects.append(project)
            done_computational = any(project.is_computational for project in done_projects)
            done_wetlab = any(project.is_wetlab for project in done_projects)
            return done_computational and done_wetlab
    return False


def value_set(column, predicate: Callable=lambda value: value, response="Permission Denied"):
    def decorator(func):
        def inner(request):
            nonlocal column
            session = request.app["session"]
            group = db_helper.get_most_recent_group(session)
            if predicate(getattr(group, column)):
                return func(request)
            return web.Response(status=403, text=response)
        return inner
    return decorator


def get_users_with_permission(app, permission_names: Union[str, Sequence[str]]) -> Set:
    rtn = set()
    if isinstance(permission_names, str):
        permission_names = (permission_names,)
    for user in db_helper.get_all_users(app["session"]):
        perms = get_user_permissions(app, user)
        for permission_name in permission_names:
            if permission_name in perms:
                rtn.add(user)
    return rtn


def get_user_permissions(app, user) -> Set:
    user_types = user.user_type.split("|")
    permissions = set()
    for user_type in user_types:
        for permission, value in app["permissions"][user_type].items():
            if value:
                permissions.add(permission)
    return permissions
