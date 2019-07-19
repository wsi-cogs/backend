"""
Copyright (c) 2017 Genome Research Ltd.

Author: Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import asyncio
from functools import wraps
import inspect
from typing import Any, Callable, ClassVar, Dict, Tuple, Union
import unittest


def async_test(fn_or_loop: Union[Callable, asyncio.BaseEventLoop, None] = None) -> Callable:
    """Decorator for testing asynchronous code.

    Runs the decorated function synchronously. Should ordinarily be used
    with AsyncTestCase.

    Can be used directly on a test method:

        @async_test
        async def test_something(self):
            ...

    Or can be passed an event loop to use:

        @async_test(my_custom_event_loop)
        async def test_something(self):
            ...
    """
    parametrised = isinstance(fn_or_loop, (asyncio.BaseEventLoop, type(None)))

    def _decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def _decorated(self, *args, **kwargs):
            loop = fn_or_loop if parametrised else self.loop
            coroutine = asyncio.coroutine(fn)
            future = coroutine(self, *args, **kwargs)
            loop.run_until_complete(future)

        return _decorated

    return _decorator if parametrised else _decorator(fn_or_loop)


class AsyncTestCase(unittest.TestCase):
    """Base class for async tests.

    Sets up an event loop at the start of each testcase, and closes the
    event loop at the end.

    Async methods must be decorated with @async_test (or similar) to
    transform them into synchronous methods, otherwise unittest won't
    run them. To avoid doing this by hand, use AsyncTestMeta.
    """

    loop: ClassVar[asyncio.BaseEventLoop]

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if not cls.loop.is_closed():
            cls.loop.call_soon(cls.loop.stop)
            cls.loop.run_forever()
            cls.loop.close()
        asyncio.set_event_loop(None)


class AsyncTestMeta(type):
    """Metaclass for async tests.

    Rewrites `async def` test functions into synchronous ones that run
    the corresponding coroutine using the testcase's event loop.

    Should be used with AsyncTestCase.

    NB: if you are using decorators (e.g. unittest.mock.patch) that
    expect and return ordinary functions (not async ones), you need to
    apply the async_test decorator by hand:

        @patch(...)
        @async_test
        async def test_something(self):
            ...

    The async_test decorator *must* be applied before any decorators
    that are not async-aware, as above.
    """

    def __new__(cls, name: str, bases: Tuple[type], namespace: Dict[str, Any]) -> type:
        assert any(issubclass(bases, AsyncTestCase) for bases in bases)
        # Make async test functions sync.
        for attr_name, attr in namespace.items():
            # XXX: this should be using the
            # unittest.TestLoader.testMethodPrefix, not "test", but it's
            # unclear how to get at the TestLoader from here.
            if attr_name.startswith("test") and inspect.iscoroutinefunction(attr):
                namespace[attr_name] = async_test(attr)
        # Create the class.
        return super().__new__(cls, name, bases, namespace)
