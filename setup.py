__copyright__ = """ Copyright (c) 2011-2012 Torsten Schmits

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

import glob

from setuptools import setup, find_packages

setup(name='tek',
      version='0.1',
      packages=find_packages(exclude=['test', 'scripts']),
      scripts=glob.glob('scripts/*'))
