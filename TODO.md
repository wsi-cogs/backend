# Todo List

The following needs to be done, in the order in which they're presented:

## Refactor Route Handlers

In progress...

* [X] `cogs/routes/email_editor.py`
* [X] `cogs/routes/export_group.py`
* [X] `cogs/routes/finalise_choices.py`
* [X] `cogs/routes/finalise_cogs.py`
* [X] `cogs/routes/group_create.py`
* [ ] `cogs/routes/group_edit_cogs.py`
* [X] `cogs/routes/login.py`
* [ ] `cogs/routes/mark_projects.py`
* [ ] `cogs/routes/project_create.py`
* [ ] `cogs/routes/project_edit.py`
* [ ] `cogs/routes/project_feedback.py`
* [ ] `cogs/routes/project_overview.py`
* [ ] `cogs/routes/resubmit_project.py`
* [X] `cogs/routes/student_upload.py`
* [X] `cogs/routes/student_vote.py`
* [X] `cogs/routes/user_overview.py`
* [X] `cogs/routes/user_page.py`

## Merge into `master`

Once the route handlers have been refactored, that is the end of the
(current) refactoring marathon and the `refactor` branch can be merged
into `master`.

## Bug Fixing from Refactor

The refactoring process will almost certainly have introduced some
obvious bugs from, e.g., typos and misunderstandings of functionality.
These should neither be subtle nor significant (i.e., they'll be easy to
find and quick to fix). The purpose of this "sprint" is to get the
refactored code to run, in the same way in which it did pre-refactor.

## Digression: `TODO`s, `FIXME`s and Docstrings

There are numerous `TODO`s and, more importantly, `FIXME`s littered
throughout the codebase. These are of varying priority and difficulty,
but ultimately should all be addressed. Any show-stopping `FIXME`s ought
to take immediate priority, but otherwise, the development of the
project's features is more important. As such, these notes largely serve
as digressions to break up the work.

Similarly, there are a lot of functions and methods with incomplete or
incorrect documentation. These are mostly listed as `TODO`s, but are
also important to complete for future maintenance efforts.

## Project Development

Develop new or existing features, as well as correcting any bugs in
existing features, per the stakeholders' requests.
