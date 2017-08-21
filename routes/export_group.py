from collections import OrderedDict
from functools import reduce
from io import BytesIO

import xlsxwriter
from aiohttp import web
from multidict import MultiDict

from db_helper import get_group


async def export_group(request):
    max_size = request.app["misc_config"]["max_export_line_length"]
    session = request.app["session"]
    series = request.match_info["group_series"]
    f_obj = BytesIO()
    with xlsxwriter.Workbook(f_obj) as workbook:
        highlighted = workbook.add_format()
        highlighted.set_bg_color("FF99FF")
        bold = workbook.add_format()
        bold.set_bg_color("FF99FF")
        bold.set_bold(True)

        worksheet = workbook.add_worksheet("feedback")
        headers = OrderedDict((("title", "Project Title"),
                               ("supervisor.name", ("Supervisor", highlighted)),
                               ("supervisor_feedback.grade", "Score"),
                               ("supervisor_feedback.good_feedback", "What did the student do particularly well?"),
                               ("supervisor_feedback.bad_feedback", "What improvements could the student make?"),
                               ("supervisor_feedback.general_feedback", "General comments on the project and report:"),
                               ("cogs_marker.name", ("CoGS Marker", highlighted)),
                               ("cogs_feedback.grade", "Score"),
                               ("cogs_feedback.good_feedback", "What did the student do particularly well?"),
                               ("cogs_feedback.bad_feedback", "What improvements could the student make?"),
                               ("cogs_feedback.general_feedback", "General comments on the project and report:")))
        names = [("", bold), ("Student name", bold)]
        students = OrderedDict()
        cells = [names]
        student_names = []
        for rotation in range(3):
            group = get_group(session, series, rotation+1)
            if group is None:
                continue
            for project in group.projects:
                if project.student:
                    student_names.append(project.student.name)
        student_names.sort()
        for name in student_names:
            students[name] = {}
        for rotation in range(3):
            group = get_group(session, series, rotation+1)
            if group is None:
                continue
            for project in sorted((project for project in group.projects if project.student), key=lambda project: project.student.name):
                student_data = students[project.student.name][rotation] = []
                for attr, header in headers.items():
                    student_data.append(header)
                    student_data.append(rgetattr(project, attr))
        for name, student in students.items():
            data = ["" for _ in next(iter(student.values()))]
            data[0] = name
            names.extend(data)
        for rotation in range(3):
            group = get_group(session, series, rotation+1)
            if group is None:
                continue
            rotation_data = [(f"Rotation {rotation + 1}", bold), ("Dates", bold)]
            cells.append(rotation_data)
            for name, student in students.items():
                if rotation not in student:
                    data = ["" for _ in next(iter(student.values()))]
                    rotation_data.extend(data)
                    continue
                rotation_data.extend(student[rotation])

        write_cells(worksheet, cells, max_size)
    f_obj.seek(0)
    return web.Response(
        headers=MultiDict({'Content-Disposition': 'Attachment'}),
        body=f_obj.read())


def write_cells(worksheet, cells, max_size):
    length_list = [min(max(len(str(row)) for row in column), max_size) for column in cells]
    for i, column in enumerate(cells):
        worksheet.set_column(i, i, length_list[i])
        for j, row in enumerate(column):
            if isinstance(row, tuple):
                worksheet.write(j, i, *row)
            else:
                worksheet.write(j, i, row)


def rgetattr(obj, attr, default=""):
    return reduce(lambda inner_obj, inner_attr: getattr(inner_obj, inner_attr, default), [obj] + attr.split('.'))
