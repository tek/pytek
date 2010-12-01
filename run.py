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

from signal import signal, SIGINT, SIG_IGN

from dispatch.interfaces import AmbiguousMethod, NoApplicableMethods

from tek.command_line import command_line
from tek.errors import MooException
from tek.tools import str_list
from tek.debug import dodebug

def moo_run(func):
    def interrupt(signum, frame):
        signal(SIGINT, SIG_IGN)
        print()
        print("Interrupted by signal %d." % signum)
        exit(1)
    if not dodebug:
        signal(SIGINT, interrupt)
    try:
        func()
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
    except MooException, e:
        command_line(e)
        if dodebug:
            raise
