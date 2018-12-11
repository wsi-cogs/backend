from aiohttp.web import Request, Response
from jinja2 import Template
import traceback

from ._format import JSONResonse, HTTPError, get_params

from cogs.common.constants import ROTATION_TEMPLATE_IDS
from cogs.mail import sanitise
from cogs.security.middleware import permit


async def get_all(request: Request) -> Response:
    """
    Get a list of templates

    :param request:
    :return:
    """
    db = request.app["db"]
    emails = db.get_all_templates()
    return JSONResonse(links={email.name: f"/api/emails/{email.name}" for email in emails},
                       items=[email.serialise() for email in emails])


async def get(request: Request) -> Response:
    """
    Get a specific template

    :param request:
    :return:
    """
    db = request.app["db"]
    template_name = request.match_info["email_name"]

    if template_name not in ROTATION_TEMPLATE_IDS:
        raise HTTPError(status=404,
                        message="Invalid email template name")

    email = db.get_template_by_name(template_name)
    return JSONResonse(links={"parent": "/api/emails"},
                       data=email.serialise())


@permit("create_project_groups")
async def edit(request: Request) -> Response:
    """
    Set the contents of a specific email template

    :param request:
    :return:
    """
    db = request.app["db"]
    template_name = request.match_info["email_name"]
    template_data = await get_params(request, {
        "subject": str,
        "content": str
    })

    try:
        subject = Template(template_data.subject)
        content = Template(template_data.content)
    except Exception:
        tb = traceback.format_exc()
        return JSONResonse(status=400,
                           status_message=tb)

    template = db.get_template_by_name(template_name)
    template.subject = template_data.subject
    template.content = sanitise(template_data.content)
    db.commit()
    return JSONResonse(status=204)
