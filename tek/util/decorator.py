__copyright__ = """ Copyright (c) 2010-2013 Torsten Schmits

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

import functools

def generated_list(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        return list(func(self, *a, **kw))
    return wrapper

def generated_sum(func, init=0):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        return sum(func(self, *a, **kw), init)
    return wrapper
