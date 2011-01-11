__copyright__ = """ Copyright (c) 2010 Torsten Schmits

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.
"""

import pkgutil

def submodules(pkg_name):
    tip = pkg_name.rsplit('.')[-1]
    pkg = __import__(pkg_name, fromlist=tip)
    for loader, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if not is_pkg:
            yield __import__('{0}.{1}'.format(pkg_name, name), fromlist=name) 
