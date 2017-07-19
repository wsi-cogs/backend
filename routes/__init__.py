from routes.index import index
from routes.project_page import project
from routes.user_overview import user_overview


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/user_overview', user_overview)
    app.router.add_get('/projects/{user_name}', project)
