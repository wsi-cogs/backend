import __main__
from project import get_most_recent_group


def deadline_scheduler(deadline):
    func_dict[deadline](__main__.app)


def student_invite(app):
    print("Inviting students")
    session = app["session"]
    group = get_most_recent_group(session)
    group.student_viewable = True
    group.student_choosable = True


func_dict = {
    "student_invite": student_invite
}
