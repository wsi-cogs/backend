from collections import defaultdict

from aiohttp_jinja2 import template

from db_helper import get_all_users, get_most_recent_group


@template('finalise_choices.jinja2')
async def finalise_choices(request):
    """
    Create a table with users and their choices for projects to join

    :param request:
    :return Response:
    """
    session = request.app["session"]
    group = get_most_recent_group(session)

    project_choice_map = defaultdict(lambda: defaultdict(lambda: []))
    for user in get_all_users(session):
        for i, option in enumerate((user.first_option, user.second_option, user.third_option)):
            if option:
                project_choice_map[option.id][i].append(user)
    for project_id, options in project_choice_map.items():
        project_choice_map[project_id]["length"] = max(len(option) for option in options.values())
    return {"projects": group.projects,
            "choices": project_choice_map}
