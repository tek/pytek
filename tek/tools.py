from __future__ import print_function

__copyright__ = """ Copyright (c) 2009-2011 Torsten Schmits

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

import sys, collections, os, logging, threading, time, urllib2
from itertools import *

from tek.log import stdouthandler, debug
from tek.io.terminal import terminal

try:
    from itertools import compress
except ImportError:
    def compress(data, selectors):
        # compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
        return (d for d, s in izip(data, selectors) if s)

def zip_fill(default, *seqs):
    # TODO itertools.zip_longest
    filler = lambda *seq: [el if el is not None else default for el in seq]
    return map(filler, *seqs)

class Silencer(object):
    """ Context manager that suppresses output to stdout. """
    def __init__(self, active=True):
        self._active = active

    def __enter__(self):
        if self._active:
            sys.stdout = self
            stdouthandler.setLevel(logging.CRITICAL)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._active:
            sys.stdout = sys.__stdout__
            stdouthandler.setLevel(logging.INFO)

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
must_not_repeat = lambda x: (isinstance(x, repeat) or is_seq(x) or
                             hasattr(x, '__len__'))
iterify = lambda x: (x if not must_repeat(x) and must_not_repeat(x) else
                     repeat(x))

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
formatted = lambda a: recursive_printer('formatted', a)

def filter_index(l, index):
    return [l[i] for i in index]

def join_lists(l):
    from operator import add
    return reduce(add, l, [])

def ijoin_lists(l):
    """ Convert the list of lists l to its elements' sums. """
    if l:
        try:
            if not all(ymap(isinstance, l, list)):
                from tek.errors import MooException
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
    return next(ifilter(pred, seq), None)

def find_iter(pred, it):
    return next(ifilter(pred, it), None)

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
    newkeys = ifilterfalse(pred, mydict)
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
            text = u'{:.2%} ({}k)'.format(self._percent, self._progress)
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

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            break
        num /= 1024.0
    return "%3.1f %s" % (num, x)

def free_space_in_dir(dir):
    f = os.statvfs(dir)
    return f.f_bfree * f.f_bsize

def resolve_redirect(url):
    return urllib2.urlopen(url).url