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

from bleach import clean
from bs4 import BeautifulSoup


# Allowed tags and attributes
_TAGS = [
    "a", "b", "blockquote", "code", "em", "i", "li", "ol", "strong",
    "ul", "font", "div", "u", "pre", "p", "h1", "h2", "h3", "h4", "h5",
    "h6", "br", "sub", "sup", "span"]

_ATTRS = [
    "align", "size", "face", "href", "title", "target", "style"]

_STYLES = ["text-align"]


def sanitise(html: str) -> str:
    """Sanitise input HTML."""
    soup = BeautifulSoup(html, features="html5lib")
    # Remove all <style> tags.
    # XXX: it is unclear why this is not handled by Bleach.
    styles = soup.findAll("style")
    for style in styles:
        style.extract()
    # Remove all non-whitelisted HTML.
    cleaned = clean(str(soup), tags=_TAGS, attributes=_ATTRS, styles=_STYLES, strip=True)
    return cleaned
