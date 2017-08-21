from routes.export_group import export_group
from routes.finalise_choices import finalise_choices, on_submit_group
from routes.finalise_cogs import finalise_cogs, on_submit_cogs
from routes.group_create import group_create
from routes.group_create import on_create as on_create_group
from routes.group_create import on_modify as on_modify_group
from routes.index import index
from routes.login import login
from routes.project_create import on_submit as on_create_project
from routes.project_create import project_create
from routes.project_edit import on_submit as on_edit
from routes.project_edit import project_edit
from routes.project_feedback import on_submit as feedback_submit
from routes.project_feedback import project_feedback
from routes.project_overview import group_overview, series_overview
from routes.project_page import project
from routes.resubmit_project import resubmit as resubmit_project
from routes.student_upload import download_file
from routes.student_upload import on_submit as on_student_file_upload
from routes.student_upload import student_upload
from routes.student_vote import on_submit as set_student_option
from routes.user_overview import user_overview
from routes.user_page import user_page


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
    app.router.add_post('/user_overview', user_overview)
    app.router.add_get('/finalise_choices', finalise_choices)
    app.router.add_post('/finalise_choices', on_submit_group)
    app.router.add_get('/finalise_cogs', finalise_cogs)
    app.router.add_post('/finalise_cogs', on_submit_cogs)
    app.router.add_get('/finalise_choices', finalise_choices)
    app.router.add_post('/finalise_choices', on_submit_group)
    app.router.add_get('/projects', group_overview)
    app.router.add_get('/projects/legacy/{group_series}/{group_part}', group_overview)
    app.router.add_get('/projects/legacy/{group_series}', series_overview)
    app.router.add_get('/projects/{project_name}', project)
    app.router.add_get('/projects/{project_name}/edit', project_edit)
    app.router.add_post('/projects/{project_name}/edit', on_edit)
    app.router.add_post('/projects/student_setoption', set_student_option)
    app.router.add_get('/project_feedback/{project_id}', project_feedback)
    app.router.add_post('/project_feedback/{project_id}', feedback_submit)
    app.router.add_get('/create_project', project_create)
    app.router.add_post('/create_project', on_create_project)
    app.router.add_get('/create_rotation', group_create)
    app.router.add_post('/create_rotation', on_create_group)
    app.router.add_post('/modify_rotation', on_modify_group)
    app.router.add_get('/resubmit/{project_id}', resubmit_project)
    app.router.add_post('/resubmit/{project_id}', on_create_project)
    app.router.add_get('/student_submit', student_upload)
    app.router.add_post('/student_submit', on_student_file_upload)
    app.router.add_get('/projects/files/{project_id}', download_file)
    app.router.add_get('/groups/{group_series}/export_group.xlsx', export_group)
