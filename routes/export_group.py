from functools import reduce
from io import BytesIO
from string import ascii_uppercase
from typing import Any, List

import xlsxwriter
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from multidict import MultiDict

from db import User
from db_helper import get_series, get_student_project_group, get_students_series
from mail import get_text
from permissions import view_only


@view_only("view_all_submitted_projects")
async def export_group(request: Request) -> Response:
    series = int(request.match_info["group_series"])
    f_obj = BytesIO()
    with xlsxwriter.Workbook(f_obj) as workbook:
        highlighted = workbook.add_format()
        highlighted.set_bg_color("FF99FF")
        bold = workbook.add_format()
        bold.set_bg_color("FF99FF")
        bold.set_bold(True)

        workbook.bold = bold
        workbook.highlighted = highlighted

        create_schedule(workbook, request.app, series)
        create_feedback(workbook, request.app, series)
        create_summary(workbook, request.app, series)
        create_checklist(workbook, request.app, series)

    f_obj.seek(0)
    return web.Response(
        headers=MultiDict({'Content-Disposition': 'Attachment'}),
        body=f_obj.read())


def create_schedule(workbook, app, series: int) -> None:
    worksheet = workbook.add_worksheet("schedule")
    max_size = app["misc_config"]["max_export_line_length"]
    session = app["session"]
    rotations = get_series(session, series)
    students = get_students_series(session, series)
    student_cells = gen_student_cells(students, series, "Student rotations")
    rotation_cells = [student_cells]
    for rotation in rotations:
        column = ["", "", "",
                  f"Rotation {rotation.part} - supervisor and project",
                  "",
                  ""]
        for student in students:
            project = get_student_project_group(session, student.id, rotation)
            if project:
                column.append(f"{project.abstract} - {project.supervisor.name}{', ' if project.small_info else ''}{project.small_info}")
            else:
                column.append("")
        rotation_cells.append(column)
    write_cells(worksheet, rotation_cells, max_size)


def create_feedback(workbook, app, series: int) -> None:
    worksheet = workbook.add_worksheet("feedback")
    max_size = app["misc_config"]["max_export_line_length"]
    session = app["session"]
    rotations = get_series(session, series)
    students = get_students_series(session, series)
    student_cells = gen_student_cells(students, series, "Student rotations", gap=16)
    rotation_cells = [student_cells]
    for rotation in rotations:
        start_date = rotation.student_choice.strftime("%d %B")
        end_date = rotation.student_complete.strftime("%d %B")
        column = ["", "", "",
                  f"Rotation {rotation.part} - supervisor and project",
                  f"{start_date} - {end_date}"]
        for student in students:
            project = get_student_project_group(session, student.id, rotation)
            supervisor_feedback = project.supervisor_feedback or Sentinel()
            if supervisor_feedback.grade_id not in (None, ""):
                supervisor_grade = ascii_uppercase[supervisor_feedback.grade_id]
            else:
                supervisor_grade = ""
            column.extend([
                f"Supervisor/s: {project.supervisor.name}{', ' if project.small_info else ''}{project.small_info}",
                f"Title: {project.title}",
                f"Score: {supervisor_grade}",
                "What did the student do particularly well?",
                get_text(supervisor_feedback.good_feedback),
                "What improvements could the student make?",
                get_text(supervisor_feedback.bad_feedback),
                "General comments on the project and report:",
                get_text(supervisor_feedback.general_feedback),
                ""
            ])
            if project.cogs_marker:
                cogs_feedback = project.cogs_feedback or Sentinel()
                if cogs_feedback.grade_id not in (None, ""):
                    cogs_grade = ascii_uppercase[cogs_feedback.grade_id]
                else:
                    cogs_grade = ""
                column.extend([
                    f"CoGS marker: {project.cogs_marker.name}",
                    f"Score: {cogs_grade}",
                    "What did the student do particularly well?",
                    get_text(cogs_feedback.good_feedback),
                    "What improvements could the student make?",
                    get_text(cogs_feedback.bad_feedback),
                    "General comments on the project and report:",
                    get_text(cogs_feedback.general_feedback)
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
                    ""
                ])
        rotation_cells.append(column)
    write_cells(worksheet, rotation_cells, max_size)


def create_summary(workbook, app, series: int) -> None:
    worksheet = workbook.add_worksheet("summary")
    max_size = app["misc_config"]["max_export_line_length"]
    session = app["session"]
    rotations = get_series(session, series)
    students = get_students_series(session, series)
    student_cells = gen_student_cells(students, series, "Student rotations - feedback score summary")
    rotation_cells = [student_cells]
    for rotation in rotations:
        s_column = ["", "", "", "", f"Rotation {rotation.part}", "Supervisor/s"]
        c_column = ["", "", "", "", "", "CoGS"]
        for student in students:
            project = get_student_project_group(session, student.id, rotation)
            if project:
                if project.supervisor_feedback is not None:
                    s_column.append(ascii_uppercase[project.supervisor_feedback.grade_id])
                else:
                    s_column.append("")
                if project.cogs_feedback is not None:
                    c_column.append(ascii_uppercase[project.cogs_feedback.grade_id])
                else:
                    c_column.append("")
            else:
                s_column.append("")
                c_column.append("")
        rotation_cells.append(s_column)
        rotation_cells.append(c_column)
    write_cells(worksheet, rotation_cells, max_size)


def create_checklist(workbook, app, series: int) -> None:
    worksheet = workbook.add_worksheet("checklist")
    max_size = app["misc_config"]["max_export_line_length"]
    session = app["session"]
    rotations = get_series(session, series)
    students = get_students_series(session, series)
    student_cells = gen_student_cells(students, series, "Student rotations - has feedback been given to the student?")
    rotation_cells = [student_cells]
    for rotation in rotations:
        uploaded_yn_col = ["", "", "", "", f"Rotation {rotation.part}", "Student Uploaded?"]
        supervisor_col = ["", "", "", "", "", "Supervisor/s"]
        supervisor_yn_col = ["", "", "", "", "", "Y/N"]
        cogs_col = ["", "", "", "", "", "CoGS"]
        cogs_yn_col = ["", "", "", "", "", "Y/N"]
        for student in students:
            project = get_student_project_group(session, student.id, rotation)
            uploaded_yn_col.append("Y" if project.uploaded else "")
            supervisor_col.append(project.supervisor.name)
            supervisor_yn_col.append("Y" if project.supervisor_feedback else "")
            if project.cogs_marker:
                cogs_col.append(project.cogs_marker.name)
                cogs_yn_col.append("Y" if project.cogs_feedback else "")
            else:
                cogs_col.append("")
                cogs_yn_col.append("")
        rotation_cells.append(uploaded_yn_col)
        rotation_cells.append(supervisor_col)
        rotation_cells.append(supervisor_yn_col)
        rotation_cells.append(cogs_col)
        rotation_cells.append(cogs_yn_col)
    write_cells(worksheet, rotation_cells, max_size)


def write_cells(worksheet, cells, max_size: int):
    length_list = [min(max(len(str(row)) for row in column), max_size) for column in cells]
    for i, column in enumerate(cells):
        worksheet.set_column(i, i, length_list[i])
        for j, row in enumerate(column):
            if isinstance(row, tuple):
                worksheet.write(j, i, *row)
            else:
                worksheet.write(j, i, row)


def gen_student_cells(students: List[User], series, title: str, gap=0) -> List[str]:
    student_cells = ["",
                     title,
                    f"Year: {series}-{series+1}",
                     "",
                     "",
                     "Student"]
    for student in students:
        student_cells.append(student.name)
        student_cells.extend([""]*gap)
    return student_cells


def rgetattr(obj: Any, attr: str, default: str="") -> Any:
    return reduce(lambda inner_obj, inner_attr: getattr(inner_obj, inner_attr, default), [obj] + attr.split('.'))


class Sentinel:
    def __init__(self):
        pass

    def __getattribute__(self, item):
        return ""
