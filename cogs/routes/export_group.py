"""
Copyright (c) 2017, 2018 Genome Research Ltd.

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


from io import BytesIO
from types import TracebackType
from typing import IO, List, MutableSequence, Sequence, Tuple, Type, Union

import xlsxwriter
from aiohttp.web import Request, Response
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet
from xlsxwriter.format import Format

from cogs.common import HTMLRenderer
from cogs.common.constants import MAX_EXPORT_LINE_LENGTH
from cogs.db.interface import Database
from cogs.db.models import User
from cogs.security.middleware import permit

_render_html = HTMLRenderer()

# Each cell is either a string or a tuple of arguments to the writer which may contain formatting
_CellT = Union[str, Tuple[str, Format]]


@permit("view_all_submitted_projects")
async def export_group(request:Request) -> Response:
    """
    Send the user an excel spreadsheet with information about current and previous rotations

    NOTE This handler should only be allowed if the current user has
    "view_all_submitted_projects" permissions
    """
    db = request.app["db"]

    series = int(request.match_info["group_series"])

    with GroupExportWriter(db, f"{request.app['config']['webserver']['service']}/projects/{{}}/download") as workbook:
        # Create worksheets
        workbook.create_schedule(series)
        workbook.create_feedback(series)
        workbook.create_summary(series)
        workbook.create_checklist(series)

    return Response(
        body    = workbook.read(),  # FIXME This should be asynchronous
        headers = {
            "Content-Disposition": 'attachment; filename="export_group.xlsx"',
            "Content-Type":        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})


# FIXME This Excel preparation class should ideally be in its own
# module, rather than conflated with the route handlers. I've left it
# here fore now, because it's specific to this handler...

# FIXME This thing is in serious need of some documentation! While the
# interface has been refactored (i.e., using a class with a context
# manager, etc.), I have not done much/anything to the methods. Many of
# them are very obtuse :P


class GroupExportWriter:
    """ Group export Excel preparation """
    _db:Database
    _open:bool
    _workbook_fd:IO[bytes]
    _workbook:Workbook

    def __init__(self, db:Database, download_link_template:str) -> None:
        """
        Constructor
        """
        self._db = db
        self._download_link_template = download_link_template
        self._open = False

        # TODO An optimisation would be to memoise or precache the
        # results of the database calls, because the same call is made
        # multiple times in each of worksheet creation methods

    def __enter__(self) -> "GroupExportWriter":
        """
        Context management: Open the file descriptor to set up the
        workbook and add cell formatters
        """
        if self._open:
            raise RuntimeError("Workbook already open")

        self._workbook_fd = fd = BytesIO()
        self._workbook = workbook = xlsxwriter.Workbook(fd)
        self._open = True

        highlighted = workbook.add_format()
        highlighted.set_bg_color("FF99FF")
        bold = workbook.add_format()
        bold.set_bg_color("FF99FF")
        bold.set_bold(True)

        # FIXME? Should these be added to the workbook object? They're
        # not used anywhere in the worksheet creation methods...
        # Usage was removed in commit e467de5066efb6095b8bb267fdf29add634a6db7
        # Appeared to be a cleanup. Maybe forgot to reimplement?
        workbook.bold = bold
        workbook.highlighted = highlighted

        return self

    def __exit__(self, exc_type:Type[BaseException], exc_val:BaseException, exc_tb:TracebackType) -> bool:
        """
        Context management exit: Close the workbook
        """
        self._open = False
        self._workbook.close()

        # Propagate exceptions
        return False

    @staticmethod
    def _gen_student_cells(students:List[User], series:int, title:str, gap:int = 0) -> List[_CellT]:
        """
        Generate the starting 6 heading rows and then a row for each student
        There are `gap` empty cells between each student
        """
        student_cells: List[_CellT] = [
            "",
            title,
            f"Year: {series}-{series + 1}",
            "",
            "",
            "Student"]

        for student in students:
            student_cells.append(student.name or "")
            student_cells.extend([""] * gap)

        return student_cells

    @staticmethod
    def _write_cells(worksheet:Worksheet, cells: List[List[_CellT]], max_size:int = MAX_EXPORT_LINE_LENGTH) -> None:
        """
        Write a 2D array of cells to a worksheet
        """
        length_list = [min(max(len(str(row)) for row in column), max_size) for column in cells]
        for i, column in enumerate(cells):
            worksheet.set_column(i, i, length_list[i])
            for j, row in enumerate(column):
                worksheet.write(j, i, *(row if isinstance(row, tuple) else (row,)))

    def read(self) -> bytes:
        """
        Read data from file descriptor
        """
        if self._open:
            raise RuntimeError("Workbook not written")

        self._workbook_fd.seek(0)
        return self._workbook_fd.read()

    def create_schedule(self, series:int) -> None:
        """
        Output the schedule for all rotations currently defined
        """
        if not self._open:
            raise RuntimeError("Workbook not open")

        worksheet = self._workbook.add_worksheet("schedule")

        db = self._db
        groups = db.get_project_groups_by_series(series)
        students = db.get_students_in_series(series)

        student_cells = self._gen_student_cells(students, series, "Student rotations")
        group_cells = [student_cells]

        for group in groups:
            columns: MutableSequence[Sequence[_CellT]] = list(zip(*[
                ["", "", "", f"Rotation {group.part} - supervisor and project", "Supervisor", ""],
                ["", "", "", "", f"Others involved", ""],
                ["", "", "", "", f"Project title", ""]
            ]))

            for student in students:
                project = db.get_projects_by_student(student, group)

                if project:
                    columns.append([
                        project.supervisor.name or "",
                        project.small_info or "",
                        project.title or "",
                    ])
                else:
                    columns.append(["", "", ""])

            group_cells.extend(zip(*columns))

        self._write_cells(worksheet, group_cells)

    def create_feedback(self, series:int) -> None:
        """
        Create a detailed table of supervisor and CoGS feedback
        """
        if not self._open:
            raise RuntimeError("Workbook not open")

        worksheet = self._workbook.add_worksheet("feedback")

        db = self._db
        groups = db.get_project_groups_by_series(series)
        students = db.get_students_in_series(series)

        student_cells = self._gen_student_cells(students, series, "Student rotations", gap=19)
        group_cells = [student_cells]

        for group in groups:
            assert group.student_choice is not None
            start_date = group.student_choice.strftime("%d %B")
            assert group.student_complete is not None
            end_date = group.student_complete.strftime("%d %B")

            column: List[_CellT] = [
                "", "", "",
                f"Rotation {group.part} - supervisor and project",
                f"{start_date} - {end_date}",
                ""
            ]

            for student in students:
                project = db.get_projects_by_student(student, group)
                if not project:
                    column.extend([
                        f"",
                        f"Supervisor/s: (No Project)",
                        f"Title: (No Project)",
                        f"Score:",
                        "What did the student do particularly well?",
                        "",
                        "What improvements could the student make?",
                        "",
                        "General comments on the project and report:",
                        "",
                        "",
                        "CoGS marker: (No Project)",
                        "Score: ",
                        "What did the student do particularly well?",
                        "",
                        "What improvements could the student make?",
                        "",
                        "General comments on the project and report:",
                        "",
                        ""
                    ])
                    continue

                supervisor_feedback = project.supervisor_feedback

                # NOTE This used to use a sentinel object (similarly,
                # below), which was quite a neat approach, but I feel
                # this is much clearer
                grade = good_feedback = bad_feedback = general_feedback = ""
                if supervisor_feedback:
                    grade = supervisor_feedback.to_grade().name
                    good_feedback = supervisor_feedback.good_feedback or ""
                    bad_feedback = supervisor_feedback.bad_feedback or ""
                    general_feedback = supervisor_feedback.general_feedback or ""

                column.extend([
                    f"Download link: {self._download_link_template.format(project.id)}",
                    f"Supervisor/s: {project.supervisor.name}{', ' if project.small_info else ''}{project.small_info}",
                    f"Title: {project.title}",
                    f"Score: {grade}",
                    "What did the student do particularly well?",
                    _render_html(good_feedback),
                    "What improvements could the student make?",
                    _render_html(bad_feedback),
                    "General comments on the project and report:",
                    _render_html(general_feedback),
                    ""
                ])

                if project.cogs_marker:
                    cogs_feedback = project.cogs_feedback

                    grade = good_feedback = bad_feedback = general_feedback = ""
                    if cogs_feedback:
                        grade = cogs_feedback.to_grade().name
                        good_feedback = cogs_feedback.good_feedback or ""
                        bad_feedback = cogs_feedback.bad_feedback or ""
                        general_feedback = cogs_feedback.general_feedback or ""

                    column.extend([
                        f"CoGS marker: {project.cogs_marker.name}",
                        f"Score: {grade}",
                        "What did the student do particularly well?",
                        _render_html(good_feedback),
                        "What improvements could the student make?",
                        _render_html(bad_feedback),
                        "General comments on the project and report:",
                        _render_html(general_feedback),
                        ""
                    ])

                else:
                    column.extend([
                        "CoGS marker: ",
                        "Score: ",
                        "What did the student do particularly well?",
                        "",
                        "What improvements could the student make?",
                        "",
                        "General comments on the project and report:",
                        "",
                        ""
                    ])

            group_cells.append(column)

        self._write_cells(worksheet, group_cells)

    def create_summary(self, series:int) -> None:
        """
        Get a summary of results for students' projects in a series
        In the form:
            Student|R1 |R2 |R3
                   |S|C|S|C|S|C
            Bob    |A|B|C|D|E|F
        """
        if not self._open:
            raise RuntimeError("Workbook not open")

        worksheet = self._workbook.add_worksheet("summary")

        db = self._db
        groups = db.get_project_groups_by_series(series)
        students = db.get_students_in_series(series)

        student_cells = self._gen_student_cells(students, series, "Student rotations - feedback score summary")
        group_cells = [student_cells]

        for group in groups:
            s_column: List[_CellT] = ["", "", "", "", f"Rotation {group.part}", "Supervisor/s"]
            c_column: List[_CellT] = ["", "", "", "", "", "CoGS"]

            for student in students:
                project = db.get_projects_by_student(student, group)

                if project:
                    if project.supervisor_feedback is not None:
                        s_column.append(project.supervisor_feedback.to_grade().name)
                    else:
                        s_column.append("")

                    if project.cogs_feedback is not None:
                        c_column.append(project.cogs_feedback.to_grade().name)
                    else:
                        c_column.append("")

                else:
                    s_column.append("")
                    c_column.append("")

            group_cells.append(s_column)
            group_cells.append(c_column)

        self._write_cells(worksheet, group_cells)

    def create_checklist(self, series:int) -> None:
        """
        Synopsis of which markers have given feedback for projects in a series
        """
        if not self._open:
            raise RuntimeError("Workbook not open")

        worksheet = self._workbook.add_worksheet("checklist")

        db = self._db
        groups = db.get_project_groups_by_series(series)
        students = db.get_students_in_series(series)

        student_cells = self._gen_student_cells(students, series, "Student rotations - has feedback been given to the student?")
        group_cells = [student_cells]

        for group in groups:
            uploaded_yn_col: List[_CellT] = ["", "", "", "", f"Rotation {group.part}", "Student Uploaded?"]
            supervisor_col: List[_CellT] = ["", "", "", "", "", "Supervisor/s"]
            supervisor_yn_col: List[_CellT] = ["", "", "", "", "", "Marked?"]
            cogs_col: List[_CellT] = ["", "", "", "", "", "CoGS"]
            cogs_yn_col: List[_CellT] = ["", "", "", "", "", "Marked?"]

            for student in students:
                project = db.get_projects_by_student(student, group)
                if not project:
                    uploaded_yn_col.append("")
                    supervisor_col.append("")
                    supervisor_yn_col.append("")
                    cogs_col.append("")
                    cogs_yn_col.append("")
                    continue

                uploaded_yn_col.append("Y" if project.uploaded else "")
                supervisor_col.append(project.supervisor.name or "")
                supervisor_yn_col.append("Y" if project.supervisor_feedback else "")

                if project.cogs_marker:
                    cogs_col.append(project.cogs_marker.name or "")
                    cogs_yn_col.append("Y" if project.cogs_feedback else "")
                else:
                    cogs_col.append("")
                    cogs_yn_col.append("")

            group_cells.append(uploaded_yn_col)
            group_cells.append(supervisor_col)
            group_cells.append(supervisor_yn_col)
            group_cells.append(cogs_col)
            group_cells.append(cogs_yn_col)

        self._write_cells(worksheet, group_cells)
