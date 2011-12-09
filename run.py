__copyright__ = """ Copyright (c) 2010-2011 Torsten Schmits

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

import signal, sys

from dispatch.interfaces import AmbiguousMethod, NoApplicableMethods

from tek import dodebug, logger
from tek.errors import MooException
from tek.tools import str_list

class SignalManager(object):
    _instance = None

    class __metaclass__(type):
        @property
        def instance(cls):
            if cls._instance is None:
                cls._instance = SignalManager()
            return cls._instance

    def __init__(self):
        if SignalManager._instance is not None:
            raise MooException('Tried to instantiate singleton SignalManager!')
        self._handlers = dict()
        self.exit_on_interrupt = True

    def sigint(self, handler):
        self.add(signal.SIGINT, handler)

    def add(self, signum, handler):
        signal.signal(signum, self.handle)
        self._handlers.setdefault(signum, []).append(handler)

    def remove(self, handler):
        for sig in self._handlers.itervalues():
            try:
                sig.remove(handler)
            except ValueError:
                pass

    def handle(self, signum, frame):
        logger.error('Interrupted by signal {}'.format(signum))
        for handler in reversed(self._handlers.get(signum, [])):
            handler(signum, frame)
        signal.signal(signum, signal.SIG_IGN)
        if signum == signal.SIGINT and self.exit_on_interrupt:
            sys.exit()

def moo_run(func, *args):
    try:
        func(*args)
    except AmbiguousMethod, e:
        parms = (e.args[1][0].__class__.__name__,
                 str_list(a.__class__.__name__ for a in e.args[1][1:]))
        print('dispatch ambiguity on a %s with argument types (%s)' % parms)
        print('ambiguous functions were: ' + str_list(f[1].__name__ for f in
                                                    e.args[0]))
        if dodebug:
            raise
    except NoApplicableMethods, e:
        parms = (e.args[0][0].__class__.__name__,
                 str_list(a.__class__.__name__ for a in e.args[0][1:]))
        print('no applicable dispatch method on a %s with argument types (%s)' %
              parms)
        if dodebug:
            raise
    except Exception, e:
        logger.error(e)
        if dodebug:
            raise
