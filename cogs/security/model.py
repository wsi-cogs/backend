"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
* Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

#from typing import Union, Collection, Callable, Set, Sequence, Optional
#
#from aiohttp import web
#from aiohttp.web import Application
#from aiohttp.web_request import Request
#from aiohttp.web_response import Response
#
#from cogs.db import functions
#from cogs.db.models import Project, ProjectGroup, User
#from cogs.common.types import Cookies

import textwrap
from typing import Dict, Type

from cogs.common.constants import PERMISSIONS


class _BaseRole(object):
    """
    Base role object
    NOTE Do not instantiate
    """
    _permissions:Dict[str, bool]

    def __init__(self, **permissions:bool) -> None:
        self._permissions = permissions

    def __eq__(self, other:"_BaseRole") -> bool:
        """ Role equivalence """
        return self.__class__ == other.__class__ \
           and all(v == other._permissions[k]
                   for k, v in self._permissions.items())

    def __or__(self, other:"_BaseRole") -> "_BaseRole":
        """ Logical disjunction of equivalent permissions """
        assert self.__class__ == other.__class__
        return self.__class__(**{k: v | other._permissions[k]
                                 for k, v in self._permissions.items()})

    # TODO Role methods go here...

def _build_role(*permissions:str) -> Type[_BaseRole]:
    """
    Build a role class with a constructor taking boolean arguments
    matching the specified permissions, with respective, read-only
    properties

    This uses the same kind of ugly metaprogramming as the standard
    library uses to build namedtuples... Approach with caution!

    :param permissions:
    :return:
    """
    assert permissions

    # Define constructor
    src = """
    class Role(_BaseRole):
        def __init__(self, *, {init_params}) -> None:
            super().__init__(**{{ {param_dict} }})
    """.format(
        init_params = ", ".join(map(lambda p: f"{p}:bool", permissions)),
        param_dict  = ", ".join(map(lambda p: f"\"{p}\": {p}", permissions))
    )

    # Define properties
    for p in permissions:
        src += """
        @property
        def {p}(self) -> bool:
            return self._permissions["{p}"]
        """.format(p=p)

    # Oh god, now I'm going to need to take a shower :P
    namespace = {"_BaseRole": _BaseRole}
    exec(textwrap.dedent(src), namespace)
    return namespace["Role"]

Role = _build_role(*PERMISSIONS)


## TODO Stuff that will (probably) need to go into _BaseRole:
## def get_permission_from_cookie(app: Application, cookies: Cookies, permission: str) -> bool:
##     """
##     Given a cookie store, return if the user is allowed a given permission.
## 
##     :param app:
##     :param app:
##     :param cookies:
##     :param permission:
##     :return:
##     """
##     user = functions.get_user_id(app, cookies)
##     if user is None:
##         return False
##     return permission in get_user_permissions(app, user)
## 
## 
## def view_only(permissions: Union[Collection[str], str]) -> Callable:
##     """
##     Returns a 403 status error is the client is not authorised to view the content.
##     Otherwise allows the function to be called as normal.
## 
##     :param permissions:
##     :return:
##     """
##     def decorator(func: Callable) -> Callable:
##         def inner(request: Request) -> Response:
##             nonlocal permissions
##             if isinstance(permissions, str):
##                 permissions = (permissions, )
##             for permission in permissions:
##                 if not get_permission_from_cookie(request.app, request.cookies, permission):
##                     return web.Response(status=403, text="Permission Denied")
##             return func(request)
##         return inner
##     return decorator
## 
## 
## def is_user(app, cookies, user: User) -> bool:
##     """
##     Return if the currently logged in user is the passed user
## 
##     :param app:
##     :param cookies:
##     :param user:
##     :return:
##     """
##     return functions.get_user_cookies(app, cookies) == user.id
## 
## 
## def can_view_group(request: Request, group: ProjectGroup) -> bool:
##     """
##     Can the logged in user view `group`?
## 
##     :param request:
##     :param group:
##     :return:
##     """
##     cookies = request.cookies
##     if functions.get_user_cookies(request.app, cookies) == -1:
##         return False
##     if get_permission_from_cookie(request.app, cookies, "view_projects_predeadline"):
##         return True
##     return group.student_viewable
## 
## 
## def can_choose_project(app: Application, cookies: Cookies, project: Project) -> bool:
##     """
##     Can the logged in user choose `project`?
## 
##     :param app:
##     :param cookies:
##     :param project:
##     :return:
##     """
##     if get_permission_from_cookie(app, cookies, "join_projects"):
##         if project.group.student_choosable:
##             if project.group.part != 3:
##                 return True
##             done_projects = functions.get_student_projects(app, cookies)
##             done_projects.append(project)
##             done_computational = any(project.is_computational for project in done_projects)
##             done_wetlab = any(project.is_wetlab for project in done_projects)
##             return done_computational and done_wetlab
##     return False
## 
## 
## def value_set(column: str, predicate: Callable=lambda value: value, response: str="Permission Denied"):
##     """
##     Only complete the request if `predicate`(most_recent_group(`column`)) returns a truthy value
## 
##     :param column:
##     :param predicate:
##     :param response:
##     :return:
##     """
##     def decorator(func):
##         def inner(request):
##             nonlocal column
##             session = request.app["session"]
##             group = functions.get_most_recent_group(session)
##             if predicate(getattr(group, column)):
##                 return func(request)
##             return web.Response(status=403, text=response)
##         return inner
##     return decorator
