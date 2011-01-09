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

import logging, os, sys

from .debug import *

logger = logging.getLogger('tek')
logger.setLevel(logging.INFO)
stdouthandler = logging.StreamHandler(sys.stdout)
stdouthandler.setLevel(logging.INFO)
logger.addHandler(stdouthandler)
if dodebug:
    logger.setLevel(logging.DEBUG)
try:
    handler = logging.FileHandler(os.path.expanduser('~/.python/log'))
    logger.addHandler(handler)
    if dodebug:
        handler.setLevel(logging.DEBUG)
except IOError:
    pass
