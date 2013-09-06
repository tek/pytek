from __future__ import print_function, absolute_import

__copyright__ = """ Copyright (c) 2009-2013 Torsten Schmits

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

"""

import sys
import collections
import os
import logging
import threading
import time
import itertools
import functools

from tek.log import stdouthandler, debug, logger
from tek.io.terminal import terminal

def zip_fill(default, *seqs):
    # TODO itertools.zip_longest
    filler = lambda *seq: [el if el is not None else default for el in seq]
    return map(filler, *seqs)

class Silencer(object):
    """ Context manager that suppresses output to stdout. """
    def __init__(self, active=True):
        self._active = active
        self._file = os.tmpfile()

    def __enter__(self):
        if self._active:
            stdouthandler.setLevel(logging.CRITICAL)
            sys.stdout = self._file
            sys.stderr = self._file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._active:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            stdouthandler.setLevel(logging.INFO)

    def write(self, data):
        pass

def repr_params(*params):
    return '(' + ', '.join(map(repr, params)) + ')'

def simple_repr(self, *params):
    return '{}{}'.format(self.__class__.__name__, repr_params(*params))

def str_list(l, j=', ', printer=lambda s: s, typ=unicode, do_filter=False):
    strings = map(printer, l)
    if do_filter:
        strings = itertools.ifilter(None, strings)
    return j.join(map(typ, strings))

def choose(lst, indicator):
    return [l for l, i in itertools.izip(lst, indicator) if i]

def make_list(*args):
    result = []
    for a in args:
        if a is not None:
            if (not isinstance(a, basestring) and
                isinstance(a, collections.Sequence)):
                result.extend(filter(lambda e: e is not None, a))
            else:
                result.append(a)
    return result

def camelcaseify(name, sep=''):
    return sep.join([n.capitalize() for n in name.split('_')])

is_seq = lambda x: (not isinstance(x, basestring) and
                    (isinstance(x, collections.Sequence) or
                     hasattr(x, '__iter__')))
must_repeat = lambda x: (isinstance(x, (basestring, type)) or
                         hasattr(x, 'ymap_repeat'))
must_not_repeat = lambda x: (isinstance(x, itertools.repeat) or is_seq(x) or
                             hasattr(x, '__len__'))
iterify = lambda x: (x if not must_repeat(x) and must_not_repeat(x) else
                     itertools.repeat(x))

def yimap(func, *args, **kwargs):
    return itertools.imap(lambda *a: func(*a, **kwargs),
                          *itertools.imap(iterify, args))

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
formatted = lambda a: recursive_printer('formatted', a)

def filter_index(l, index):
    return [l[i] for i in index]

def join_lists(l):
    from operator import add
    return reduce(add, l, [])

def cumsum(seq):
    sum = 0
    for element in seq:
        sum += seq
        yield sum

def ijoin_lists(l):
    """ Convert the list of lists l to its elements' sums. """
    if l:
        try:
            if not all(ymap(isinstance, l, list)):
                from tek.errors import MooException
                raise MooException('Some elements aren\'t lists!')
            for i in cumsum([0] + map(len, l[:-1])):
                l[i:i+1] = l[i]
        except Exception as e:
            logger.debug('ijoin_lists failed with: ' + str(e))
    return l

def pairs(list1, list2):
    for e1 in list1:
        for e2 in list2:
            yield e1, e2

def indices_of(pred, seq):
    return (i for i, e in enumerate(seq) if pred(e))

def index_of(pred, seq):
    return next(indices_of(pred, seq), None)

def find(pred, seq, default=None):
    return next(itertools.ifilter(pred, seq), default)

def find_iter(pred, it):
    return next(itertools.ifilter(pred, it), None)

def listdir_abs(dirname):
    return [os.path.join(dirname, f) for f in os.listdir(dirname)]

def decode(string):
    try:
        return unicode(string)
    except UnicodeDecodeError:
        return unicode(string, encoding='utf-8')

enc = sys.getfilesystemencoding()

def unicode_filename(string):
    if not isinstance(string, unicode):
        string = unicode(string, encoding=enc)
    return string

def extremum_len(fun, *seqs):
    return fun(map(len, seqs))

def minlen(*seqs):
    return extremum_len(min, *seqs)

def maxlen(*seqs):
    return extremum_len(max, *seqs)

def filterfalse_keys(pred, mydict):
    newkeys = itertools.ifilterfalse(pred, mydict)
    return dict([[k, mydict[k]] for k in newkeys])

def list_diff(l1, l2):
    return list(set(l1) - set(l2))

def list_uniq_ordered(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]

class ProgressPrinter(threading.Thread):
    def __init__(self, source, dest):
        self._target_size = os.path.getsize(source)
        self._destination = dest
        self._running = False
        self._file_size = 0.
        threading.Thread.__init__(self)

    def run(self):
        self._running = True
        while self._running:
            self._print_progress()
            time.sleep(1)

    def _print_progress(self):
        if os.path.isfile(self._destination):
            self._file_size = os.path.getsize(self._destination)
            text = '{:.2%} ({}k)'.format(self._percent, self._progress)
            terminal.pop()
            terminal.push(text)
            terminal.flush()

    @property
    def _percent(self):
        return self._file_size / self._target_size

    @property
    def _progress(self):
        return self._file_size / 1024.

    def stop(self):
        self._running = False

    def finish(self):
        self._progress = self._file_size
        self._percent = 1.
        self._print_progress()
        self.stop()

def copy_progress(source, dest):
    import shutil, signal
    old_handler = signal.getsignal(signal.SIGINT)
    dest_file = (os.path.join(dest, os.path.basename(source)) if
                 os.path.isdir(dest) else dest)
    progress = ProgressPrinter(source, dest_file)
    def interrupt(signum, frame):
        progress.stop()
        signal(signal.SIGINT, old_handler)
        print()
        print("Interrupted by signal %d." % signum)
    signal.signal(signal.SIGINT, interrupt)
    terminal.lock()
    terminal.push_lock()
    progress.start()
    shutil.copy(source, dest)
    progress.finish()
    terminal.pop_lock()

def sizeof_fmt(num, prec=1, bi=True):
    div = 1024. if bi else 1000.
    fmt = '{{:3.{}f}} {{}}'.format(prec)
    for x in ['B','KB','MB','GB','TB']:
        if num < div:
            break
        num /= div
    return fmt.format(num, x)

def free_space_in_dir(dir):
    f = os.statvfs(dir)
    return f.f_bfree * f.f_bsize

def resolve_redirect(url):
    try:
        import requests
    except ImportError:
        return url
    else:
        return requests.get(url, stream=True).url

def lists_uniq(lists):
    return list(set(sum(lists, [])))

class _WrapThread(threading.Thread):

    def __init__(self, function):
        threading.Thread.__init__(self)
        self._function = function
        self.result = None

    def run(self):
        self.result = self._function()

def parallel_map(func, *a):
    partials = [functools.partial(func, *args) for args in itertools.izip(*a)]
    threads = map(_WrapThread, partials)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return [thread.result for thread in threads]
