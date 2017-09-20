from typing import Dict

from aiohttp.web_request import Request
from aiohttp_jinja2 import template

from db_helper import get_project_id, get_navbar_data


@template('project_edit.jinja2')
def resubmit(request: Request) -> Dict:
    session = request.app["session"]
    project_id = int(request.match_info["project_id"])
    project = get_project_id(session, project_id)
    programmes = request.app["misc_config"]["programmes"]
    return {"project": project,
            "label": "Create",
            "programmes": programmes,
            "cur_option": "create_project",
            **get_navbar_data(request)}
