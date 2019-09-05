"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
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

import os.path

from cogs.common import logging
from cogs.db.models import Project


class FileHandler(logging.LogWriter):
    """Project file handling interface."""

    _upload_dir: str
    _max_filesize: int

    def __init__(self, upload_directory: str, max_filesize: int) -> None:
        self._upload_dir = os.path.normpath(os.path.expanduser(upload_directory))
        self._max_filesize = max_filesize

    def get_max_filesize(self):
        return self._max_filesize

    def get_filename_for_project(self, project: Project) -> str:
        """Return the filename for the report for the given project.

        Note that this does not guarantee that said file exists.
        """
        group = project.group
        return os.path.join(
            self._upload_dir,
            f"{project.student.id}",
            f"{group.series}_{group.part}_{project.id}.zip"
        )

    def get_project(self, project, mode):
        """Obtain a file handle for a project's file.

        This should be used in the same way as open(), i.e.:

        >>> with get_project(...) as f:
        ...     ...
        """
        user_path = os.path.join(self._upload_dir, str(project.student.id))
        if not os.path.isdir(user_path):
            os.makedirs(user_path)

        return open(self.get_filename_for_project(project), mode=mode)
