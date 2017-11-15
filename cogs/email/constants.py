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

# E-mail signature appended to all e-mails
SIGNATURE = """
    <br><br>
    Best regards,<br>
    Graduate Programme<br>
    <a href="mailto:gradoffice@sanger.ac.uk">gradoffice@sanger.ac.uk</a>
"""

# Deadline extension template prepended to all invitation e-mails in the
# event of... you guessed it: a deadline extension!
DEADLINE_EXTENSION_TEMPLATE = """
    The deadline has been extended to {{ new_deadline.strftime('%d/%m/%Y') }}
    due to too few projects being submitted.<br><br><hr><br>
"""
