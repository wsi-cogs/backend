"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>

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

from aiohttp.web import Application

from .email_editor import email_edit
from .email_editor import on_edit as on_email_edit
from .export_group import export_group
from .finalise_choices import finalise_choices, on_submit_group
from .view_choices import view_choices
from .finalise_cogs import finalise_cogs, on_submit_cogs
from .group_create import group_create
from .group_create import on_create as on_create_group
from .group_create import on_modify as on_modify_group
from .group_edit_cogs import edit_cogs
from .group_edit_cogs import on_submit_cogs as edit_cogs_submit
from .login import login
from .project_create import on_submit as on_create_project
from .project_create import project_create
from .project_edit import on_delete as on_delete_project
from .project_edit import on_submit as on_edit_project
from .project_edit import project_edit
from .project_feedback import on_submit as feedback_submit
from .project_feedback import project_feedback
from .project_overview import group_overview, series_overview
from .resubmit_project import resubmit as resubmit_project
from .student_upload import download_file
from .student_upload import on_submit as on_student_file_upload
from .student_upload import student_upload
from .student_vote import on_submit as set_student_option
from .user_overview import user_overview
from .user_page import user_page
from .mark_projects import markable_projects

import cogs.routes.api as api


def setup(app:Application) -> None:
    """
    Set up all the routes for the application

    :param app:
    :return:
    """
    # Just for testing - is implicitly disabled in production as /login leads to actual login page
    app.router.add_post('/login', login)

    app.router.add_get('/', user_page)

    app.router.add_get('/api/series', api.series.get_all)
    app.router.add_post('/api/series', api.rotations.create)

    app.router.add_get('/api/series/rotations', api.rotations.get_all)
    app.router.add_route('*', '/api/series/latest', api.rotations.latest)
    app.router.add_get('/api/series/{group_series}', api.series.get)
    app.router.add_get('/api/series/{group_series}/{group_part}', api.rotations.get)
    app.router.add_put('/api/series/{group_series}/{group_part}', api.rotations.edit)

    app.router.add_post('/api/projects', api.projects.create)
    app.router.add_get('/api/projects/{project_id}', api.projects.get)
    app.router.add_put('/api/projects/{project_id}', api.projects.edit)
    app.router.add_delete('/api/projects/{project_id}', api.projects.delete)
    app.router.add_post('/api/projects/{project_id}/mark', api.projects.mark)
    app.router.add_get('/api/projects/{project_id}/file', download_file)

    app.router.add_get('/api/users', api.users.get_all)
    app.router.add_post('/api/users', api.users.create)
    app.router.add_route('*', '/api/users/me', api.users.me)
    app.router.add_put('/api/users/me/vote', api.users.vote)
    app.router.add_get('/api/users/{user_id}', api.users.get)
    app.router.add_put('/api/users/{user_id}', api.users.edit)

    app.router.add_get('/api/emails', api.emails.get_all)
    app.router.add_get('/api/emails/{email_name}', api.emails.get)
    app.router.add_put('/api/emails/{email_name}', api.emails.edit)


    app.router.add_get('/user_overview', user_overview)
    app.router.add_post('/user_overview', user_overview)

    app.router.add_get('/email_edit', email_edit)
    app.router.add_post('/email_edit', on_email_edit)

    app.router.add_get('/finalise_choices', finalise_choices)
    app.router.add_post('/finalise_choices', on_submit_group)

    app.router.add_get('/finalise_cogs', finalise_cogs)
    app.router.add_post('/finalise_cogs', on_submit_cogs)
    app.router.add_put('/finalise_cogs', edit_cogs_submit)

    app.router.add_get('/view_choices', view_choices)

    app.router.add_get('/projects', group_overview)

    app.router.add_get('/projects/legacy/{group_series}/{group_part}', group_overview)

    app.router.add_get('/projects/legacy/{group_series}', series_overview)

    app.router.add_get('/projects/{project_name}/edit', project_edit)
    app.router.add_post('/projects/{project_name}/edit', on_edit_project)
    app.router.add_delete('/projects/{project_name}/edit', on_delete_project)

    app.router.add_post('/projects/student_setoption', set_student_option)

    app.router.add_get('/project_feedback/{project_id}', project_feedback)
    app.router.add_post('/project_feedback/{project_id}', feedback_submit)

    app.router.add_get('/markable_projects', markable_projects)

    app.router.add_get('/create_project', project_create)
    app.router.add_post('/create_project', on_create_project)

    app.router.add_get('/create_rotation', group_create)
    app.router.add_post('/create_rotation', on_create_group)

    app.router.add_post('/groups/{group_part}/modify', on_modify_group)

    app.router.add_get('/resubmit/{project_id}', resubmit_project)
    app.router.add_post('/resubmit/{project_id}', on_create_project)

    app.router.add_get('/student_submit', student_upload)
    app.router.add_post('/student_submit', on_student_file_upload)

    app.router.add_get('/projects/files/{project_id}', download_file)

    app.router.add_get('/groups/{group_series}/export_group.xlsx', export_group)

    app.router.add_get('/groups/{group_part}/edit_cogs', edit_cogs)
    app.router.add_post('/groups/{group_part}/edit_cogs', edit_cogs_submit)
