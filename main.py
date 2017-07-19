from aiohttp import web
import os
from db import init_pg, close_pg
from config.config import load_config
from routes import setup_routes
from aiohttp_session import setup as setup_cookiestore
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session import SimpleCookieStorage

app = web.Application()
setup_routes(app)

conf = load_config(os.path.join("config", "config.yaml"))
app['db_config'] = conf["db"]

#setup_cookiestore(app, EncryptedCookieStorage(conf["webserver"]["cookie_key"].encode()))
setup_cookiestore(app, SimpleCookieStorage())
del conf["webserver"]["cookie_key"]

app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)
web.run_app(app, **conf["webserver"])