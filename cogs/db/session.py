"""
Copyright (c) 2019 Genome Research Ltd.

Authors:
* Josh Holland <jh36@sanger.ac.uk>

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

from contextvars import ContextVar
from typing import Any

from sqlalchemy.util import ThreadLocalRegistry


_MISSING = object()
_context: ContextVar[Any] = ContextVar("_context", default=_MISSING)


class ContextLocalRegistry(ThreadLocalRegistry):
    """A SQLAlchemy registry, intended to store per-context sessions.

    This is designed to be used with SQLAlchemy's scoped_session, in
    order to avoid sharing a single session between multiple
    asynchronous contexts (since the session is not safe for use in this
    way). It's loosely based upon the existing ScopedRegistry and
    ThreadLocalRegistry, but is compatible with asyncio as well as with
    threaded environments.

    The intended use looks something like this:

    >>> session_factory = sessionmaker(...)
    >>> Session = scoped_session(session_factory)
    >>> Session.registry = ContextLocalRegistry(session_factory)
    >>> # then, in a request:
    >>> session = Session()
    >>> do_database_things(session)
    >>> # the Session can also be used directly, without instantiation:
    >>> Session.query(...).filter(...).all()
    >>> # and at the end of the request (e.g. in a middleware):
    >>> Session.remove()

    Note that it's safe to call `Session.remove()` even if the Session
    hasn't been used in that context, so a middleware that runs after
    every request is an ideal place to do so.

    See the SQLAlchemy documentation for more details:
    <https://docs.sqlalchemy.org/en/13/orm/contextual.html>
    """
    # TODO: it would be nice to upstream this, potentially?

    def __init__(self, createfunc):
        self.createfunc = createfunc

    def __call__(self):
        value = _context.get()
        if value is _MISSING:
            value = self.createfunc()
            _context.set(value)
        return value

    def has(self):
        return _context.get() is not _MISSING

    def set(self, value):
        _context.set(value)

    def clear(self):
        # Probably clearer/cleaner to call .reset(token) here, but it's
        # not obvious where to store the token.
        _context.set(_MISSING)
