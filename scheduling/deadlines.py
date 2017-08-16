import __main__

from db_helper import get_most_recent_group
from scheduling.grace_deadline import grace_deadline


def deadline_scheduler(deadline, *args):
    func_dict[deadline](__main__.app, *args)


def student_invite(app):
    print("Inviting students")
    session = app["session"]
    group = get_most_recent_group(session)
    group.student_viewable = True
    group.student_choosable = True


func_dict = {
    "student_invite": student_invite,
    "grace_deadline": grace_deadline
}
