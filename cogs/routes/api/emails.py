import traceback

from aiohttp.web import Request, Response
from jinja2.exceptions import TemplateError

from ._format import JSONResonse, HTTPError, get_params

from cogs.common.constants import ROTATION_TEMPLATE_IDS
from cogs.mail import sanitise
from cogs.security.middleware import permit


async def get_all(request: Request) -> Response:
    """
    Get a list of templates
    """
    db = request.app["db"]
    emails = db.get_all_templates()
    return JSONResonse(links={email.name: f"/api/emails/{email.name}" for email in emails},
                       items=[email.serialise() for email in emails])


async def get(request: Request) -> Response:
    """
    Get a specific template
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
    """
    db = request.app["db"]
    mail = request.app["mailer"]
    template_name = request.match_info["email_name"]
    template_data = await get_params(request, {
        "subject": str,
        "content": str
    })

    try:
        subject = mail.environment.from_string(template_data.subject)
    except TemplateError as e:
        # We don't want to frighten the user with a pages-long traceback or a
        # confusing exception name if we can help it.
        err = e.args[0] if e.args else type(e).__name__
        message = f"""\
Error in email subject:
  {template_data.subject}
{err}"""
        return JSONResonse(status=400, status_message=message)

    try:
        content = mail.environment.from_string(sanitise(template_data.content))
    except TemplateError as e:
        # Although long tracebacks are scary and unhelpful, it's useful to know
        # on which line the error is located, so we attempt to extract that
        # information from the traceback.
        err = e.args[0] if e.args else type(e).__name__
        lineno = None
        tb = getattr(e, "__traceback__", None)
        while tb is not None:
            # This is how Jinja2 itself identifies its own frames:
            # https://github.com/pallets/jinja/blob/9550dc8/jinja2/debug.py#L59
            if "__jinja_template__" in tb.tb_frame.f_globals:
                lineno = tb.tb_lineno
            tb = getattr(tb, "tb_next", None)
        lines = template_data.content.splitlines()
        if lineno is not None and lineno - 1 < len(lines):
            line = lines[lineno - 1]
            message = f"""\
Error on line {lineno} of email content:
  {line}
{err}"""
        else:
            message = f"""\
Error in email content:
{err}"""
        return JSONResonse(status=400, status_message=message)

    template = db.get_template_by_name(template_name)
    template.subject = template_data.subject
    template.content = sanitise(template_data.content)
    db.commit()
    return JSONResonse(status=204)
