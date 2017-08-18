import __main__

from scheduling.grace_deadline import grace_deadline
from scheduling.student_invite import student_invite


async def deadline_scheduler(deadline, *args):
    await func_dict[deadline](__main__.app, *args)



func_dict = {
    "student_invite": student_invite,
    "grace_deadline": grace_deadline
}
