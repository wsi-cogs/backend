from typing import Dict

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_jinja2 import template

from db_helper import get_templates, get_template_name, get_navbar_data
from mail import clean_html
from permissions import view_only


@template('email_edit.jinja2')
@view_only("create_project_groups")
async def email_edit(request: Request) -> Dict:
    """
    Edit an email
    This view should only be allowed if the current user has 'create_projects'

    :param request:
    :return:
    """
    templates = get_templates(request.app["session"])
    return {"templates": templates,
            "cur_option": "email_edit",
            **get_navbar_data(request)}


@view_only("create_project_groups")
async def on_edit(request: Request) -> Response:
    """
    Edit an email
    This view should only be allowed if the current user has 'create_projects'

    :param request:
    :return:
    """
    session = request.app["session"]
    post = await request.post()
    filename = post["name"]
    assert filename in request.app["config"]["misc"]["email_whitelist"]
    template = get_template_name(session, filename)
    template.subject = post["subject"]
    template.content = clean_html(post["data"])
    session.commit()

    return web.Response(status=200, text=f"/email_edit")
