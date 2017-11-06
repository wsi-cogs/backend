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

from os import path

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import SimpleCookieStorage
from aiohttp_session import setup as setup_cookiestore
from jinja2 import FileSystemLoader

from config import load_config
from db import init_pg, close_pg
from decrypt import init_blowfish
from routes import setup_routes
from scheduling import setup as setup_scheduler


if __name__ == '__main__':
    app = web.Application()
    setup_routes(app)

    conf = load_config(path.join("config", "config.yaml"))
    app["db"] = conf["db"]
    app["deadlines"] = conf["deadlines"]
    app["login_db"] = conf["login_db"]

    aiohttp_jinja2.setup(app, loader=FileSystemLoader("./template/"))
    app.router.add_static("/static/", "./static")

    setup_cookiestore(app, SimpleCookieStorage())
    app["webserver"] = conf["webserver"]
    app["permissions"] = conf["permissions"]
    app["misc_config"] = conf["misc"]
    app["email"] = conf["email"]

    app.on_startup.append(init_pg)
    app.on_startup.append(setup_scheduler)
    app.on_startup.append(init_blowfish)
    app.on_cleanup.append(close_pg)
    web.run_app(app,
                host=conf["webserver"]["host"],
                port=conf["webserver"]["port"])
