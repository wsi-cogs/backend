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

import os

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import SimpleCookieStorage
from aiohttp_session import setup as setup_cookiestore
from jinja2 import FileSystemLoader

from cogs import config
from cogs.db import service as db
from cogs.email import Postman

from .routes import setup_routes
from .scheduling import setup as setup_scheduler


if __name__ == "__main__":
    app = web.Application()
    setup_routes(app)

    # Configuration from environment > project root
    config_file = os.getenv("COGS_CONFIG", "config.yaml")
    configuration = config.load(config_file)

    # TODO We probably don't need to thread the entire configuration
    # through the whole application; better to create app level
    # instances of things that have already consumed that state
    app["config"] = configuration

    try:
        from cogs.auth.pagesmith import PagesmithAuthenticator
        app["auth"] = PagesmithAuthenticator(configuration["pagesmith_auth"])

    except ModuleNotFoundError:
        # NOTE For debugging purposes only!
        from cogs.auth.dummy import DummyAuthenticator
        print("Pagesmith authentication not supported. Allowing everyone as root.")
        app["auth"] = DummyAuthenticator()

    # TODO Database needs to be abstracted so we can inject it as a
    # dependency for modules that need it (i.e., most of them), rather
    # than have it as an app level global

    app["mailer"] = Postman(database=None,
                            sender=configuration["email"]["sender"],
                            **configuration["email"]["smtp"])

    aiohttp_jinja2.setup(app, loader=FileSystemLoader("cogs/templates/"))
    app.router.add_static("/static/", "cogs/static")

    setup_cookiestore(app, SimpleCookieStorage())

    app.on_startup.append(db.start)
    app.on_startup.append(setup_scheduler)
    app.on_cleanup.append(db.stop)
    web.run_app(app, host=app["config"]["webserver"]["host"],
                     port=app["config"]["webserver"]["port"])
