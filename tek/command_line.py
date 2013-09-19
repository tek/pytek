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

from tek.io.terminal import TerminalController
from tek.tools import str_list, pretty, short

from crystalmethod import multimethod

class CommandLine(object):
    term = TerminalController()
    level_colors = ['green', 'cyan', 'red', 'yellow']
    prompt = ''
    suffix = '>'
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

    def pretty(self, *msgs):
        return self.recursive_print(pretty, msgs)

    def short(self, *msgs):
        return self.recursive_print(short, msgs)

    def recursive_print(self, printer, msgs):
        return self(str_list(msgs, j=' ', printer=printer))

    @multimethod(list)
    def print_(self, msg):
        list(map(self.print_, msg))

    @multimethod(object)
    def print_(self, msg):
        list(map(self.print_line, str(msg).splitlines()))

    def print_line(self, line):
        if isinstance(line, str):
            line = line.encode('utf-8')
        if self.prompt:
            print('{} {}'.format(self.prompt, line))
        else:
            print(line)

    def reconstruct_prompt(self):
        def prompter(lp, s):
            l, p = lp
            return self.color(l) + str(p) + s + self.term.NORMAL
        self.prompt = str_list(list(map(prompter, enumerate(self.prefixes),
                                        self.suffixes)), ' ')

command_line = CommandLine()

class PrefixPrinter(object):
    def __init__(self, prefix='', suffix=None):
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        command_line.level_up(self.prefix, self.suffix)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        command_line.level_down()

    def __call__(self, msg):
        command_line.print_(msg)

    def pretty(self, msg):
        self(pretty(msg))
