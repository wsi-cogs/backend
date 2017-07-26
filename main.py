import os

from aiohttp import web
import aiohttp_jinja2
from jinja2 import FileSystemLoader
from aiohttp_session import setup as setup_cookiestore
#from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session import SimpleCookieStorage

from db import init_pg, close_pg
from config.config import load_config
from routes import setup_routes


def main():
    """
    Launch the app

    :return:
    """
    app = web.Application()
    setup_routes(app)

    conf = load_config(os.path.join("config", "config.yaml"))
    app['db_config'] = conf["db"]

    aiohttp_jinja2.setup(app, loader=FileSystemLoader("./template/"))
    app.router.add_static("/static/", "./static")

    # TODO: Move to encrypted cookie store once testing is complete
    #setup_cookiestore(app, EncryptedCookieStorage(conf["webserver"]["cookie_key"].encode()))
    setup_cookiestore(app, SimpleCookieStorage())
    del conf["webserver"]["cookie_key"]
    app["permissions"] = conf["permissions"]

    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    web.run_app(app, **conf["webserver"])

if __name__ == '__main__':
    main()
