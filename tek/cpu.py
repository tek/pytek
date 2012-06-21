__copyright__ = """ Copyright (c) 2012 Torsten Schmits

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

import resource, functools

from tek import logger

class CPUTimer(object):
    enabled = True

    def __init__(self, label='cpu time', log=True):
        self._label = label
        self._log = log

    @property
    def _current(self):
        return resource.getrusage(resource.RUSAGE_SELF)[0]

    def __enter__(self):
        self._start = self._current

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end = self._current
        if self._log and self.enabled:
            logger.info('{}: {}s'.format(self._label, self.time))

    @property
    def time(self):
        return self._end - self._start

def timed(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        with CPUTimer(label='{}.{}'.format(self.__class__.__name__,
                                           func.__name__)):
            return func(self, *a, **kw)
    return wrapper
