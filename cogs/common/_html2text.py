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

from typing import Callable, ClassVar

from html2text import HTML2Text


class HTMLRenderer(Callable[[str], str]):
    """ Render HTML as text """
    _formatter:ClassVar[HTML2Text] = HTML2Text()
    _formatter.body_width = 65
    _formatter.use_automatic_links = True

    def __call__(self, html:str) -> str:
        return HTMLRenderer._formatter.handle(html)
