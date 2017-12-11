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
import sys

import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader

from cogs import __version__, auth, config, routes
from cogs.common import logging
from cogs.db.interface import Database
from cogs.email import Postman
from cogs.file_handler import FileHandler
from cogs.scheduler import Scheduler


_noop = lambda *_, **__: None

if __name__ == "__main__":
    # Configuration from environment > project root
    config_file = os.getenv("COGS_CONFIG", "config.yaml")
    c = config.load(config_file)

    logging_level = getattr(logging, c["general"]["logging_level"].upper(), logging.DEBUG)
    logger = logging.initialise(logging_level)
    logger.info(f"Starting CoGS v{__version__}")

    app = web.Application(logger=logger, middlewares=[auth.middleware,
                                                      routes.middleware])

    app["db"] = db = Database(**c["database"])
    app["mailer"] = mail = Postman(database=db, sender=c["email"]["sender"], **c["email"]["smtp"])
    app["file_handler"] = file_handler = FileHandler(c["general"]["upload_directory"], int(c["general"]["max_filesize"]))

    app["scheduler"] = scheduler = Scheduler(db, mail, file_handler)
    if "reset_db" in sys.argv:
        # NOTE For debugging purposes only!
        logger.warning("Removing all previously scheduled jobs.")
        scheduler.reset_all()

    try:
        from cogs.auth.pagesmith import PagesmithAuthenticator
        app["auth"] = PagesmithAuthenticator(db, c["pagesmith_auth"])

    except ModuleNotFoundError:
        # NOTE For debugging purposes only!
        from cogs.auth.dummy import DummyAuthenticator
        logger.warning("Pagesmith authentication not supported. Allowing everyone as root.")
        app["auth"] = DummyAuthenticator(db)

    routes.setup(app)
    aiohttp_jinja2.setup(app, loader=FileSystemLoader("cogs/routes/templates"))
    app.router.add_static("/static/", "static")

    web.run_app(app, host=c["webserver"]["host"], port=c["webserver"]["port"],
                     access_log=logger, access_log_format="%a \"%r\" %s %b",
                     print=_noop)
