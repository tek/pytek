__copyright__ = """ Copyright (c) 2011 Torsten Schmits

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

import sys, pkgutil
from tek import logger
from tek.config import Configurations

def write_pkg_config(dir, outfile):
    sys.path[:0] = [dir]
    Configurations.allow_files = False
    Configurations.allow_override = False
    mods = pkgutil.walk_packages([dir], onerror=lambda x: True)
    configs = (name for l, name, ispkg in mods
               if not ispkg and name.rsplit('.', 1)[-1] == 'config')
    for name in configs:
        try:
            mod = __import__(name)
            if hasattr(mod, 'reset_config'):
                mod.reset_config(reset_parent=False)
        except Exception as e:
            logger.debug(e)
    Configurations.write_config(outfile)
