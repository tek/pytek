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

from tek.terminal import TerminalController
from tek.tools import str_list, pretty, short
from dispatch import generic, on
from dispatch.strategy import Signature

class CommandLine(object):
    term = TerminalController()
    level_colors = ['green', 'cyan', 'red', 'yellow']
    prompt = ''
    suffix = '>>>'
    prefixes = []
    suffixes = []

    def color(self, level):
        c = self.level_colors[level % len(self.level_colors)]
        return getattr(self.term, c.upper())

    def level_up(self, prefix='', suffix=None):
        suffix = self.suffix if suffix is None else suffix
        self.prefixes.append(prefix)
        self.suffixes.append(suffix)
        self.reconstruct_prompt()

    def level_down(self, count=1):
        del self.prefixes[-count:]
        del self.suffixes[-count:]
        self.reconstruct_prompt()

    def __call__(self, msg):
        return self.print_(msg)

    def pretty(self, msg):
        return self(pretty(msg))

    def short(self, msg):
        return self(short(msg))

    @generic()
    def print_(self, msg):
        """ print stuff with a nested prompt.

        """

    @print_.when(Signature(msg=list))
    def print_(self, msg):
        map(self.print_, msg)

    @print_.when(Signature())
    def print_(self, msg):
        map(self.print_line, unicode(msg).split('\n'))

    def print_line(self, line):
        if isinstance(line, unicode):
            line = line.encode('utf-8')
        if self.prompt:
            print(self.prompt, line)
        else:
            print(line)
        #if type(line) != unicode:
            #line = unicode(line)
        #print(self.prompt, line.encode('utf-8'))

    def reconstruct_prompt(self):
        prompter = lambda (l, p), s: self.color(l) + unicode(p) + s + \
                   self.term.NORMAL
        self.prompt = str_list(map(prompter, enumerate(self.prefixes),
                                   self.suffixes), ' ')

command_line = CommandLine()

class PrefixPrinter(object):
    def __init__(self, prefix='', suffix=None):
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        command_line.level_up(self.prefix, self.suffix)

    def __exit__(self, exc_type, exc_value, traceback):
        command_line.level_down()

    def __call__(self, msg):
        command_line.print_(msg)

    def pretty(self, msg):
        self(pretty(msg))
