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

import sys, collections, operator, os
from itertools import *

try:
    from numpy import cumsum
except:
    cumsum = lambda s: reduce(lambda a, b: a + [a[-1] + b], s[1:], s[:1])

from dispatch.interfaces import AmbiguousMethod, NoApplicableMethods

from tek.errors import MooException
from tek.debug import debug

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

def str_list(l, j=', ', printer=lambda s: s, typ=unicode, do_filter=False):
    strings = map(printer, l)
    if do_filter:
        strings = ifilter(None, strings)
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

def camelcaseify(name):
    return ''.join([n.capitalize() for n in name.split('_')])

is_seq = lambda x: not isinstance(x, (str, unicode)) and \
                   (isinstance(x, collections.Sequence) or
                    hasattr(x, '__iter__'))
must_repeat = lambda x: isinstance(x, (str, unicode, type)) or \
                        hasattr(x, 'ymap_repeat')
must_not_repeat = lambda x: isinstance(x, repeat) or is_seq(x) or \
                            hasattr(x, '__len__')
iterify = lambda x: x if not must_repeat(x) and must_not_repeat(x) else \
                    repeat(x)

def yimap(func, *args, **kwargs):
    return imap(lambda *a: func(*a, **kwargs), *imap(iterify, args))

def ymap(*args, **kwargs):
    return list(yimap(*args, **kwargs))

def recursive_printer(name, arg):
    if hasattr(arg, name):
        return getattr(arg, name)
    elif is_seq(arg):
        return '[' + str_list(arg, printer=lambda a: 
                              recursive_printer(name, a)) + ']'
    else:
        return unicode(arg)

pretty = lambda a: recursive_printer('pretty', a)
short = lambda a: recursive_printer('short', a)

def filter_index(l, index):
    return [l[i] for i in index]

def moo_run(func):
    try:
        func()
    except AmbiguousMethod, e:
        parms = (e.args[1][0].__class__.__name__, str_list(a.__class__.__name__
                                                           for a in e.args[1][1:]))
        print('dispatch ambiguity on a %s with argument types (%s)' % parms)
        print('ambiguous functions were: ' + str_list(f[1].__name__ for f in
                                                    e.args[0]))
        raise
    except NoApplicableMethods, e:
        parms = (e.args[0][0].__class__.__name__, str_list(a.__class__.__name__
                                                           for a in e.args[0][1:]))
        print('no applicable dispatch method on a %s with argument types (%s)' %
              parms)
        raise
    except MooException, e:
        print(e)

def join_lists(l):
    return reduce(operator.add, l, [])

def ijoin_lists(l):
    """ Convert the list of lists l its elements' sums.

    """
    if l:
        try:
            if not all(ymap(isinstance, l, list)):
                raise MooException('Some elements aren\'t lists!')
            for i in cumsum([0] + map(len, l[:-1])):
                l[i:i+1] = l[i]
        except Exception, e:
            debug('ijoin_lists failed with: ' + str(e))
    return l

def pairs(list1, list2):
    for e1 in list1:
        for e2 in list2:
            yield e1, e2

def index_of(pred, seq):
    return next((i for i, e in enumerate(seq) if pred(e)), None)

def find(pred, seq):
    i = index_of(pred, seq)
    return seq[i] if i is not None else i

def find_iter(pred, it):
    return next(ifilter(pred, it), None)

def listdir_abs(dirname):
    return [os.path.join(dirname, f) for f in os.listdir(dirname)]
