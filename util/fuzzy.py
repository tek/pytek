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

from tek import logger

from difflib import SequenceMatcher
from operator import itemgetter

def best_match(seq, target):
    matcher = SequenceMatcher()
    matcher.set_seq2(target)
    def ratio():
        for index, specimen in enumerate(seq):
            matcher.set_seq1(specimen) 
            yield index, matcher.ratio()
    return max(ratio(), key=itemgetter(1))
