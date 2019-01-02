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
import aiohttp_cors

from .export_group import export_group

from . import api


def setup(app:Application) -> None:
    """
    Set up all the routes for the application

    :param app:
    :return:
    """
    app.router.add_get('/api/series', api.series.get_all)
    app.router.add_post('/api/series', api.rotations.create)

    app.router.add_get('/api/series/rotations', api.rotations.get_all)
    app.router.add_get('/api/series/latest', api.rotations.latest)
    app.router.add_put('/api/series/latest', api.rotations.latest)
    app.router.add_get('/api/series/{group_series}', api.series.get)
    app.router.add_get('/api/series/{group_series}/export.xlsx', export_group)
    app.router.add_get('/api/series/{group_series}/{group_part}/remind', api.rotations.remind)
    app.router.add_get('/api/series/{group_series}/{group_part}', api.rotations.get)
    app.router.add_put('/api/series/{group_series}/{group_part}', api.rotations.edit)

    app.router.add_post('/api/projects', api.projects.create)
    app.router.add_put('/api/projects/set_cogs', api.projects.set_cogs)
    app.router.add_get('/api/projects/{project_id}', api.projects.get)
    app.router.add_put('/api/projects/{project_id}', api.projects.edit)
    app.router.add_delete('/api/projects/{project_id}', api.projects.delete)
    app.router.add_post('/api/projects/{project_id}/mark', api.projects.mark)
    app.router.add_get('/api/projects/{project_id}/mark', api.projects.get_marks)
    app.router.add_put('/api/projects/{project_id}/file', api.projects.upload)
    app.router.add_get('/api/projects/{project_id}/file', api.projects.download)
    app.router.add_get('/api/projects/{project_id}/file/status', api.projects.upload_information)

    app.router.add_get('/api/users', api.users.get_all)
    app.router.add_post('/api/users', api.users.create)
    app.router.add_get('/api/users/me', api.users.me)
    app.router.add_put('/api/users/me', api.users.me)
    app.router.add_get('/api/users/permissions', api.users.get_with_permission)
    app.router.add_put('/api/users/assign_projects', api.users.assign_projects)
    app.router.add_post('/api/users/unset_votes', api.users.unset_votes)
    app.router.add_put('/api/users/me/vote', api.users.vote)
    app.router.add_get('/api/users/{user_id}', api.users.get)
    app.router.add_put('/api/users/{user_id}', api.users.edit)

    app.router.add_get('/api/emails', api.emails.get_all)
    app.router.add_get('/api/emails/{email_name}', api.emails.get)
    app.router.add_put('/api/emails/{email_name}', api.emails.edit)

    app.router.add_get('/api/util/status/{}', api.util.get_status)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)
