from routes.index import index
from routes.project_page import project
from routes.user_overview import user_overview
from routes.project_overview import group_overview, series_overview
from routes.project_edit import project_edit
from routes.login import login


def setup_routes(app):
    """
    Sets up all the routes for the webapp.

    :param app:
    :return:
    """
    app.router.add_get('/', index)
    app.router.add_post('/login', login)
    app.router.add_get('/user_overview', user_overview)
    app.router.add_get('/projects', group_overview)
    app.router.add_get('/projects/legacy/{group_series}/{group_part}', group_overview)
    app.router.add_get('/projects/legacy/{group_series}', series_overview)
    app.router.add_get('/projects/{project_name}', project)
    app.router.add_get('/projects/{project_name}/edit', project_edit)
