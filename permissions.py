from typing import Union, Collection
from datetime import date
from aiohttp import web


def get_permission_from_cookie(cookies, permission: str):
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


def is_user(cookies, user):
    """
    Return if the currently logged in user is the passed user

    :param cookies:
    :param user_id:
    :return:
    """
    return int(cookies.get("user_id", "-1")) == user.id


def can_view_group(request, group):
    cookies = request.cookies
    if get_permission_from_cookie(cookies, "view_projects_predeadline"):
        return True
    if group.student_invite is None:
        return False
    now = date.today()
    return now > group.student_invite
