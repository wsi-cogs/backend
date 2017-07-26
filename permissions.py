from typing import Union, Collection
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
                    return web.Response(status=403)
            return func(request)
        return inner
    return decorator


def is_user_id(cookies, user_id):
    """
    Return if the currently logged in user has the passed id

    :param cookies:
    :param user_id:
    :return:
    """
    return int(cookies.get("user_id", "-1")) == user_id
