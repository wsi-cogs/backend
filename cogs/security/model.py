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


# FIXME The following functions are either redundant or should be
# moved/refactored into something more appropriate


# FIXME This function simply checks the cookie against a given user, to
# check they match. This should be part of authentication middleware,
# which also probably belongs in this module.

# def is_user(app, cookies, user: User) -> bool:
#     """
#     Return if the currently logged in user is the passed user
# 
#     :param app:
#     :param cookies:
#     :param user:
#     :return:
#     """
#     return functions.get_user_cookies(app, cookies) == user.id


# FIXME This decorator is like an ad hoc version of the one above
# (view_only), where the 403 response is determined by specific state in
# the data model. This seems hacky to me; the permissions model should
# cover all use cases, so this shouldn't be needed at all.

# def value_set(column: str, predicate: Callable=lambda value: value, response: str="Permission Denied"):
#     """
#     Only complete the request if `predicate`(most_recent_group(`column`)) returns a truthy value
# 
#     :param column:
#     :param predicate:
#     :param response:
#     :return:
#     """
#     def decorator(func):
#         def inner(request):
#             nonlocal column
#             session = request.app["session"]
#             group = functions.get_most_recent_group(session)
#             if predicate(getattr(group, column)):
#                 return func(request)
#             return web.Response(status=403, text=response)
#         return inner
#     return decorator
