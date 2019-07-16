# Internals documentation

## How emails are sent

`project_selected_student`

- sent in `cogs.routes.api.users.unset_votes`, which is executed when project
  choices are finalised by the grad office
  - sent to every student who has been assigned to a project

`project_selected_supervisor`

- also sent in `cogs.routes.api.users.unset_votes`
  - sent to all supervisors with projects in this rotation

`supervisor_student_project_list`

- also sent in `cogs.routes.api.users.unset_votes`
  - sent to all supervisors

`feedback_given`

- sent in `cogs.routes.api.projects.mark`, which is executed when a project is
  marked (either by a supervisor or by a CoGS member)
  - sent to the student whose project has just been marked
  - also sent to all members of the grad office

`cogs_not_found`

- sent in `cogs.routes.api.projects.upload`, which is executed when a project
  report is uploaded
- sent to all members of the grad office, iff the project has no CoGS marker and
  this was the first time the project was uploaded

`supervisor_invite_{n}`

- sent in `cogs.routes.api.rotation.create`, which is executed when a rotation
  is created
  - sent to all supervisors
- sent in `cogs.routes.api.rotations.edit`, which is executed when a rotation is
  edited
  - sent to all supervisors, iff the deadline for supervisors to submit their
    projects has changed (with a hard-coded header mentioning the change)
- sent in `cogs.routes.api.rotations.remind`, which is executed when a member of
  the grad office presses the button to remind all supervisors of the project
  submission deadline
  - sent to all supervisors

`supervisor_submit_grad_office`

- sent in `cogs.scheduler.jobs.supervisor_submit`, which is executed when the
  deadline for supervisors to submit projects passes
  - sent to all members of the grad office

`student_invite_{n}`

- sent in `cogs.scheduler.jobs.student_invite`, which is executed when students
  are invited to view the available projects
  - sent to all students

`can_set_projects`

- sent in `cogs.scheduler.jobs.student_choice`, which is executed when the
  deadline for students to make their project choices passes
  - sent to all members of the grad office

`student_uploaded`

- sent in `cogs.scheduler.jobs.grace_deadline`, which is executed when a
  project's grace period (the time in which the student can re-upload a report)
  is over
  - sent to the project supervisor and the CoGS marker
- sent in `cogs.scheduler.jobs.mark_project`, which is executed by the deadline
  machinery (TODO -- scheduled by itself, and also by
  `cogs.scheduler.jobs.grace_deadline`, which is executed either one or three
  days after the deadline for students to upload projects)
  - sent to the user (supervisor or marker) who needs to mark this project, iff
    they have not yet marked the project

### Pesters

The function `cogs.scheduler.jobs.pester` sends various different emails.

- scheduled to run at "pester times", which vary for each deadline
- scheduled whenever a "group" deadline is scheduled, based on said "pester
  times"
- uses a particular template for each deadline's pester emails, or the
  `pester_generic` template if no specific template was defined

## Deadlines

There's a (probably historical) distinction between "group" and "user"
deadlines; group deadlines are triggered by the passing of the five dates
attached to a rotation, whereas user deadlines are nominally those that are
relevant to some particular user (but really they are just all the deadlines
that aren't caused by the passing of a rotation deadline).

This distinction has existed since 411e7e6 ("Separate deadlines into user and
group").

<!-- vim: set tw=80: -->
