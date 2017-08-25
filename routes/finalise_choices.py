from collections import defaultdict

from aiohttp import web
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
    user_ids = []
    for user in get_all_users(session):
        for i, option in enumerate((user.first_option, user.second_option, user.third_option)):
            if option:
                project_choice_map[option.id][i].append(user)
                if str(user.id) not in user_ids:
                    user_ids.append(str(user.id))
    for project_id, options in project_choice_map.items():
        for option in options.values():
            option.sort(key=lambda user: user.priority, reverse=True)
        project_choice_map[project_id]["length"] = max(len(option) for option in options.values())
    return {"projects": group.projects,
            "choices": project_choice_map,
            "user_ids": user_ids}


async def on_submit_group(request):
    session = request.app["session"]
    post = await request.post()
    group = get_most_recent_group(session)
    for project in group.projects:
        if str(project.id) not in post:
            project.student_id = None
        else:
            project.student_id = int(post[str(project.id)])
    session.commit()
    return web.Response(status=200, text="/finalise_cogs")
