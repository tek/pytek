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
from tek.tools import str_list

class CommandLine(object):
    term = TerminalController()
    level_colors = ['green', 'cyan', 'red', 'yellow']
    prompt = ''
    suffix = '>>>'
    prefixes = []

    @classmethod
    def color(self, level):
        c = self.level_colors[level % len(self.level_colors)]
        return getattr(self.term, c.upper())

    @classmethod
    def level_up(self, prefix=''):
        self.prefixes.append(prefix)
        self.reconstruct_prompt()

    @classmethod
    def level_down(self, count=1):
        del self.prefixes[-count:]
        self.reconstruct_prompt()

    @classmethod
    def print_(self, msg):
        if hasattr(msg, '__iter__'):
            map(self.print_, msg)
        else:
            map(self.print_line, unicode(msg).split('\n'))

    @classmethod
    def print_line(self, line):
        print(self.prompt + unicode(line))

    @classmethod
    def reconstruct_prompt(self):
        prompter = lambda (l, p): self.color(l) + unicode(p) + self.suffix + \
                   self.term.NORMAL
        self.prompt = str_list(map(prompter, enumerate(self.prefixes)), ' ') + \
                      ' '

class PrefixPrinter(object):
    def __init__(self, prefix=''):
        self.prefix = prefix

    def __enter__(self):
        CommandLine.level_up(self.prefix)

    def __exit__(self, exc_type, exc_value, traceback):
        CommandLine.level_down()
