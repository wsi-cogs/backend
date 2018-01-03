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

from typing import List, NamedTuple


# FIXME This is directly lifted from the configuration. Not all fields
# are necessary (probably) and this could generally do with tidying up
# and documenting properly...

class Deadline(NamedTuple):
    """ Model for deadline metadata """
    name:str

    # FIXME I feel as though the below could be simplified
    pester_times:List[int]       = []
    pester_permissions:List[str] = []
    pester_content:str           = ""
    pester_template:str          = ""
    pester_predicate:str         = ""
