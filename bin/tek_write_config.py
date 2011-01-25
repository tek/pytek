#! /usr/bin/env python

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

if __name__ == '__main__':
    import os, pkgutil, sys
    from tek.config import Configurations
    from tek.util.module import submodules
    assert(len(sys.argv) == 3)
    try:
        from config import reset_config
        reset_config(register_files=False, reset_parent=False)
    except ImportError:
        pass
    dirs = filter(os.path.isdir, os.listdir(sys.argv[1]))
    for dir in dirs:
        try:
            for mod in submodules(dir):
                if mod.__name__.endswith('.config'):
                    if hasattr(mod, 'reset_config'):
                        mod.reset_config(register_files=False,
                                         reset_parent=False)
        except (ImportError, ValueError):
            pass
    Configurations.write_config(sys.argv[2])
