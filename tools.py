""" {{{ Copyright (c) 2009 Torsten Schmits

This file is part of pytek. pytek is free software;
you can redistribute it and/or modify it under the terms of the GNU General
Public License version 2, as published by the Free Software Foundation.

pytek is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA  02111-1307  USA

}}} """

from __future__ import print_function

import sys
from itertools import izip, imap, repeat

def zip_fill(default, *seqs):
    # TODO itertools.zip_longest
    filler = lambda *seq: [el if el is not None else default for el in seq]
    return map(filler, *seqs)

class Silencer(object):
    """ Context manager that suppresses output to stdout.

    """
    def __enter__(self):
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = sys.__stdout__

    def write(self, data):
        pass

def repr_params(*params):
    return '(' + ', '.join(map(repr, params)) + ')'

def str_list(l, j=', ', printer=lambda s: s, typ=unicode):
    strings = map(printer, l)
    return j.join(map(typ, strings))

def choose(lst, indicator):
    return [l for l, i in izip(lst, indicator) if i]

def make_list(*args):
    result = []
    for a in args:
        if a is not None:
            if isinstance(a, list):
                result.extend(filter(lambda e: e is not None, a))
            else:
                result.append(a)
    return result

must_repeat = lambda x: isinstance(x, (str, unicode)) or hasattr(x, 'ymap_repeat')
must_not_repeat = lambda x: isinstance(x, repeat) or hasattr(x, '__len__') or hasattr(x, '__iter__')
iterify = lambda x: x if not must_repeat(x) and must_not_repeat(x) else repeat(x)

def yimap(func, *args, **kwargs):
    return imap(lambda *a: func(*a, **kwargs), *imap(iterify, args))

def ymap(*args, **kwargs):
    return list(yimap(*args, **kwargs))

def pretty(arg):
    if hasattr(arg, 'pretty'):
        return arg.pretty
    elif isinstance(arg, list):
        return str_list(arg, printer=pretty)
    else:
        return unicode(arg)

def short(arg):
    if hasattr(arg, 'short'):
        return arg.short
    elif isinstance(arg, list):
        return str_list(arg, printer=short)
    else:
        return unicode(arg)
