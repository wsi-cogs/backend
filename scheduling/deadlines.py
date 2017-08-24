from datetime import timedelta

import __main__

from scheduling.grace_deadline import grace_deadline
from scheduling.pester import pester
from scheduling.student_invite import student_invite


async def deadline_scheduler(deadline, *args):
    await func_dict[deadline](__main__.app, *args)


def schedule_deadline(app, group, deadline_id, time):
    scheduler = app["scheduler"]
    pester_dates = app["misc_config"]["pester_time"]
    scheduler.add_job(deadline_scheduler,
                      "date",
                      id=f"{group.series}_{group.part}_{deadline_id}",
                      args=(deadline_id,),
                      run_date=time,
                      replace_existing=True)
    for delta_day in pester_dates:
        #FIXME Change seconds to days
        scheduler.add_job(deadline_scheduler,
                          "date",
                          id=f"pester_{delta_day}_{group.series}_{group.part}_{deadline_id}",
                          args=("pester", deadline_id, delta_day),
                          run_date=time - timedelta(seconds=delta_day),
                          replace_existing=True)


func_dict = {
    "student_invite": student_invite,
    "grace_deadline": grace_deadline,
    "pester": pester,
}
