import __main__

from db_helper import get_most_recent_group
from scheduling.grace_deadline import grace_deadline


async def deadline_scheduler(deadline, *args):
    await func_dict[deadline](__main__.app, *args)


async def student_invite(app):
    print("Inviting students")
    session = app["session"]
    group = get_most_recent_group(session)
    group.student_viewable = True
    group.student_choosable = True


func_dict = {
    "student_invite": student_invite,
    "grace_deadline": grace_deadline
}
