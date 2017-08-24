from aiohttp_jinja2 import template

from db_helper import get_project_id


@template('project_edit.jinja2')
def resubmit(request):
    session = request.app["session"]
    project_id = int(request.match_info["project_id"])
    project = get_project_id(session, project_id)
    programmes = request.app["misc_config"]["programmes"]
    return {"project": project, "label": "Create", "programmes": programmes}
