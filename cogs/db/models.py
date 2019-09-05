"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
* Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from datetime import date
from functools import reduce
from typing import Dict, Optional

from sqlalchemy import Integer, String, Column, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from cogs.common.constants import GRADES
from cogs.scheduler.constants import DEADLINES
from cogs.security.model import Role
from cogs.security import roles


# TODO: many/most of the columns defined here should have nullable=False.


def _base_repr(self):
    """
    Monkeypatch the Base object so it's eval-able
    """
    # TODO: why(!)?
    params = ", ".join("{}={}".format(column.key, repr(getattr(self, column.key)))
                       for column in self.__table__.columns)

    return f"{self.__class__.__name__}({params})"


Base = declarative_base()
Base.__repr__ = _base_repr  # type: ignore


class ProjectGroup(Base):
    """Represents a single rotation."""

    __tablename__          = "project_groups"

    id                     = Column(Integer, primary_key=True)
    supervisor_submit      = Column(Date)
    student_invite         = Column(Date)
    student_choice         = Column(Date)
    student_complete       = Column(Date)
    marking_complete       = Column(Date)
    series                 = Column(Integer)
    part                   = Column(Integer)
    student_viewable       = Column(Boolean)
    student_choosable      = Column(Boolean)
    student_uploadable     = Column(Boolean)
    can_finalise           = Column(Boolean)
    read_only              = Column(Boolean)  # Can supervisors modify the projects in this group
    manual_supervisor_reminders = Column(Date)

    projects               = relationship("Project", uselist=True)

    def can_solicit_project(self, user: "User") -> bool:
        """Can the user be asked to provide a project for this rotation?

        Only if they haven't submitted one already.
        """
        return not any((project.supervisor == user) for project in self.projects)

    def serialise(self):
        """Produce a JSON-ready dict representing the rotation."""
        serialised = {}
        dates = {}
        ids = 0
        for key in self.__table__.columns.keys():
            value = getattr(self, key)
            if key == "manual_supervisor_reminders":
                serialised["manual_supervisor_reminders"] = value and value.strftime("%Y-%m-%d")
            elif isinstance(value, date):
                dates[key] = {"name": DEADLINES[key].name,
                              "value": value.strftime("%Y-%m-%d"),
                              "id": ids}
                ids += 1
            else:
                serialised[key] = value
        serialised["deadlines"] = dates

        return serialised


class ProjectGrade(Base):
    """Represents feedback from one user on a single project."""

    __tablename__          = "project_grades"

    id                     = Column(Integer, primary_key=True)
    grade_id               = Column(Integer)
    good_feedback          = Column(String)
    bad_feedback           = Column(String)
    general_feedback       = Column(String)

    def to_grade(self) -> GRADES:
        """Convert the stored grade ID into a grade enum member."""
        assert self.grade_id is not None
        return list(GRADES)[self.grade_id]

    def serialise(self):
        """Produce a JSON-ready dict representing the feedback."""
        return {"grade": self.to_grade().name,
                "good_feedback": self.good_feedback,
                "general_feedback": self.general_feedback,
                "bad_feedback": self.bad_feedback}


class Project(Base):
    """Represents a single project."""

    __tablename__          = "projects"

    id                     = Column(Integer, primary_key=True)
    title                  = Column(String)
    small_info             = Column(String)
    abstract               = Column(String)
    is_computational       = Column(Boolean)
    is_wetlab              = Column(Boolean)
    programmes             = Column(String) # Pipe seperated list of programmes

    uploaded               = Column(Boolean)
    grace_passed           = Column(Boolean)

    supervisor_id          = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    cogs_marker_id         = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    student_id             = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    group_id               = Column(Integer, ForeignKey(ProjectGroup.id, ondelete="CASCADE"))

    supervisor_feedback_id = Column(Integer, ForeignKey(ProjectGrade.id, ondelete="CASCADE"))
    cogs_feedback_id       = Column(Integer, ForeignKey(ProjectGrade.id, ondelete="CASCADE"))

    supervisor             = relationship("User", foreign_keys=supervisor_id, back_populates="projects_as_supervisor", post_update=True)
    cogs_marker            = relationship("User", foreign_keys=cogs_marker_id, back_populates="projects_as_cogs_marker", post_update=True)
    student                = relationship("User", foreign_keys=student_id, back_populates="projects_as_student", post_update=True)
    group                  = relationship(ProjectGroup, foreign_keys=group_id)
    supervisor_feedback    = relationship(ProjectGrade, foreign_keys=supervisor_feedback_id)
    cogs_feedback          = relationship(ProjectGrade, foreign_keys=cogs_feedback_id)

    def can_solicit_feedback(self, user: "User") -> bool:
        """Can the user be pestered to provide feedback for the project?

        Only if the user is the project's supervisor or CoGS marker and
        their feedback hasn't been completed already.
        """
        if user == self.supervisor:
            return self.supervisor_feedback_id is None

        elif user == self.cogs_marker:
            return self.cogs_feedback_id is None

        return False

    def serialise(self, include_mark_ids):
        """Produce a JSON-ready dict representing the project."""
        serialised = {key: getattr(self, key) for key in self.__table__.columns.keys() if (
            include_mark_ids or key not in {"supervisor_feedback_id", "cogs_feedback_id"}
        )}
        if serialised["programmes"]:
            serialised["programmes"] = serialised["programmes"].split("|")
        else:
            serialised["programmes"] = []
        return serialised


class User(Base):
    """Represents a user of the system."""

    __tablename__          = "users"

    id                     = Column(Integer, primary_key=True)
    name                   = Column(String)
    user_type              = Column(String)

    # TODO Constraints: email or email_personal may be NULL, but not
    # simultaneously; user addresses (whichever exist) must be unique
    email                  = Column(String)  # Sanger e-mail, if they have one
    email_personal         = Column(String)  # Personal e-mail

    priority               = Column(Integer)

    first_option_id        = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    second_option_id       = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    third_option_id        = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))

    first_option           = relationship(Project, foreign_keys=first_option_id, post_update=True)
    second_option          = relationship(Project, foreign_keys=second_option_id, post_update=True)
    third_option           = relationship(Project, foreign_keys=third_option_id, post_update=True)

    projects_as_supervisor = relationship(Project, foreign_keys=Project.supervisor_id, back_populates="supervisor", uselist=True)
    projects_as_cogs_marker = relationship(Project, foreign_keys=Project.cogs_marker_id, back_populates="cogs_marker", uselist=True)
    projects_as_student = relationship(Project, foreign_keys=Project.student_id, back_populates="student", uselist=True)

    @property
    def role(self) -> Role:
        """
        Get the user's permissions based on the disjunction of their
        roles, deserialised from their user type
        """
        assert self.user_type is not None
        return reduce(
            lambda acc, this: acc | this,
            [getattr(roles, role) for role in self.user_type.split("|") if role],
            roles.zero)

    @property
    def best_email(self) -> Optional[str]:
        """
        Return the user's Sanger e-mail address, if it exists, otherwise
        fallback to their personal address
        """
        return self.email or self.email_personal

    def can_view_group(self, group: ProjectGroup) -> bool:
        """Can the user view the given rotation?

        Only if the user's role allows them, or the group is visible to
        all users.
        """
        return bool(
            self.role.view_projects_predeadline
            or group.student_viewable
        )

    def can_choose_project(self, project: Project) -> bool:
        """Can the given user (student) choose the specified project?

        Only if their role allows and, for their final project, they've
        done at least one computational and one experimental project
        (the project must also not be assigned to another student).
        """
        if self.role.join_projects:
            if project.student is not None and self != project.student:
                # Students can't choose projects which other students have
                # already been assigned to.
                return False

            if project.group.part != 3:
                # If it's not the final rotation,
                # then the student can pick any project
                return True

            all_projects = [project] + [
                p for p in self.projects_as_student
                if p.group.series == project.group.series]

            done_computational = any(p.is_computational for p in all_projects)
            done_wetlab = any(p.is_wetlab for p in all_projects)

            return done_computational and done_wetlab

        return False

    def serialise(self):
        """Produce a JSON-ready dict representing the user."""
        serialised = {key: getattr(self, key) for key in self.__table__.columns.keys()}
        if serialised["user_type"]:
            serialised["user_type"] = serialised["user_type"].split("|")
        else:
            serialised["user_type"] = []
        serialised["permissions"] = self.role.serialise()
        return serialised


class EmailTemplate(Base):
    """Represents an email template (subject and contents)."""

    __tablename__          = "email_templates"

    id                     = Column(Integer, primary_key=True)
    name                   = Column(String)

    subject                = Column(String)
    content                = Column(String)

    def serialise(self):
        """Produce a JSON-ready dict representing the template."""
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}


__all__ = [
    "ProjectGroup",
    "ProjectGrade",
    "Project",
    "User",
    "EmailTemplate",
]
