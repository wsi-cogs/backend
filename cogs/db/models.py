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
from typing import Dict

from sqlalchemy import Integer, String, Column, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


def _base_repr(self):
    """
    Monkeypatch the Base object so it's eval-able

    :param self:
    :return str:
    """
    params = ", ".join("{}={}".format(column.key, repr(getattr(self, column.key)))
                       for column in self.__table__.columns)

    return f"{self.__class__.__name__}({params})"

Base = declarative_base()
Base.__repr__ = _base_repr


class ProjectGroup(Base):
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

    projects               = relationship("Project")

    @property
    def dates(self) -> Dict[str, date]:
        """
        Return a dictionary containing all the dates associated with a
        project group

        FIXME Why do we need this? We can already do, e.g.,
        mygroup.student_invite; why do we also need to be able to do
        mygroup.dates["student_invite"]? The only thing this does
        outside of this is to do type introspection on the columns
        (i.e., so it returns all the columns that are dates, without
        having to hardcode them).

        NOTE The function from which this was originally derived
        (get_dates_from_group)

        :return:
        """
        # FIXME? I only assume I can check the column's type like this
        # from a brief scan through the documentation. Moreover, this
        # doesn't do exactly what the original get_dates_from_group
        # function supposedly did; that seems to return all columns and
        # just formats any dates as %d/%m/%Y strings...
        return {
            column.key: getattr(self, column.key)
            for column in self.__table__.columns
            if isinstance(column.type, Date)}

    def can_solicit_project(self, user:"User") -> bool:
        """
        Can the user be pestered to provide a project in the current
        project group? Only if they haven't submitted one already

        :param user:
        :return:
        """
        return not any((project.supervisor == user) for project in self.projects)


class ProjectGrade(Base):
    __tablename__          = "project_grades"

    id                     = Column(Integer, primary_key=True)
    grade_id               = Column(Integer)
    good_feedback          = Column(String)
    bad_feedback           = Column(String)
    general_feedback       = Column(String)


class Project(Base):
    __tablename__          = "projects"

    id                     = Column(Integer, primary_key=True)
    title                  = Column(String)
    small_info             = Column(String)
    abstract               = Column(String)
    is_computational       = Column(Boolean)
    is_wetlab              = Column(Boolean)
    programmes             = Column(String)

    uploaded               = Column(Boolean)
    grace_passed           = Column(Boolean)

    supervisor_id          = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    cogs_marker_id         = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    student_id             = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    group_id               = Column(Integer, ForeignKey(ProjectGroup.id, ondelete="CASCADE"))

    supervisor_feedback_id = Column(Integer, ForeignKey(ProjectGrade.id, ondelete="CASCADE"))
    cogs_feedback_id       = Column(Integer, ForeignKey(ProjectGrade.id, ondelete="CASCADE"))

    supervisor             = relationship("User",       foreign_keys=supervisor_id, post_update=True)
    cogs_marker            = relationship("User",       foreign_keys=cogs_marker_id, post_update=True)
    student                = relationship("User",       foreign_keys=student_id, post_update=True)
    group                  = relationship(ProjectGroup, foreign_keys=group_id)
    supervisor_feedback    = relationship(ProjectGrade, foreign_keys=supervisor_feedback_id)
    cogs_feedback          = relationship(ProjectGrade, foreign_keys=cogs_feedback_id)

    def is_read_only(self, user:"User") -> bool:
        """
        Is the project read only? Inherited from its project group and
        by virtue of the user being the project's supervisor

        :param user:
        :return:
        """
        is_supervisor = (user == self.supervisor)
        return self.group.read_only or not is_supervisor

    def can_resubmit(self, user:"User", current_group:ProjectGroup) -> bool:
        """
        Can the project be resubmitted? Only if it's in the current,
        read only project group and the user's its supervisor

        :param user:
        :param current_group:
        :return:
        """
        is_supervisor = (user == self.supervisor)
        return self.group == current_group \
           and self.group.read_only \
           and is_supervisor

    def can_mark(self, user:"User") -> bool:
        """
        Can the project be marked? Only if its grace time has passed and
        the user can be pestered for feedback

        :param user:
        :return:
        """
        return self.can_solicit_feedback(user) if self.grace_passed else False

    def can_solicit_feedback(self, user:"User") -> bool:
        """
        Can the user be pestered to provide feedback for the project?
        Only if the user is the project's supervisor or CoGS marker and
        their feedback hasn't been completed already

        :param user:
        :return:
        """
        if user == self.supervisor:
            return self.supervisor_feedback_id is None

        elif user == self.cogs_marker:
            return self.cogs_feedback_id is None

        return False


class User(Base):
    __tablename__          = "users"

    id                     = Column(Integer, primary_key=True)
    name                   = Column(String)
    email                  = Column(String)
    user_type              = Column(String)

    priority               = Column(Integer)

    first_option_id        = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    second_option_id       = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))
    third_option_id        = Column(Integer, ForeignKey(Project.id, ondelete="SET NULL"))

    first_option           = relationship(Project, foreign_keys=first_option_id, post_update=True)
    second_option          = relationship(Project, foreign_keys=second_option_id, post_update=True)
    third_option           = relationship(Project, foreign_keys=third_option_id, post_update=True)


class EmailTemplate(Base):
    __tablename__          = "email_templates"

    id                     = Column(Integer, primary_key=True)
    name                   = Column(String)

    subject                = Column(String)
    content                = Column(String)
