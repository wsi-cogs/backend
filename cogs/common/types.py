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

from typing import Awaitable, Callable

from aiohttp import web
from multidict import MultiDictProxy


# Type definition for HTTP request handler
# For reasons of "design decisions", StreamResponse is the base class, not Response:
# https://docs.aiohttp.org/en/stable/web_reference.html#response-classes
Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]

# Alias for cookies, returned by aiohttp.web.BaseRequest.cookies
Cookies = MultiDictProxy

URL = str
