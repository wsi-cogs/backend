from routes.index import index
from routes.project_page import project
from routes.user_overview import user_overview
from routes.user_page import user_page
from routes.project_overview import group_overview, series_overview
from routes.project_edit import project_edit
from routes.project_edit import on_submit as on_edit
from routes.project_create import project_create
from routes.project_create import on_submit as on_create
from routes.group_create import group_create
from routes.login import login


def setup_routes(app):
    """
    Sets up all the routes for the webapp.

    :param app:
    :return:
    """
    app.router.add_get('/', index)
    app.router.add_post('/login', login)
    app.router.add_get('/dashboard', user_page)
    app.router.add_get('/user_overview', user_overview)
    app.router.add_get('/projects', group_overview)
    app.router.add_get('/projects/legacy/{group_series}/{group_part}', group_overview)
    app.router.add_get('/projects/legacy/{group_series}', series_overview)
    app.router.add_get('/projects/{project_name}', project)
    app.router.add_get('/projects/{project_name}/edit', project_edit)
    app.router.add_post('/projects/{project_name}/edit', on_edit)
    app.router.add_get('/create_project', project_create)
    app.router.add_post('/create_project', on_create)
    app.router.add_get('/create_group', group_create)
