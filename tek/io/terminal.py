__copyright__ = """ Copyright (c) 2010-2013 Torsten Schmits

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

import termios
import fcntl
import sys
import os
import re
from time import sleep

from multimethods import multimethod

from tek.log import logger, debug

class TerminalController(object):
    """
    A class that can be used to portably generate formatted output to
    a terminal.  
    
    `TerminalController` defines a set of instance variables whose
    values are initialized to the control sequence necessary to
    perform a given action.  These can be simply included in normal
    output to the terminal:

        >>> term = TerminalController()
        >>> print 'This is '+term.GREEN+'green'+term.NORMAL

    Alternatively, the `render()` method can used, which replaces
    '${action}' with the string required to perform 'action':

        >>> term = TerminalController()
        >>> print term.render('This is ${GREEN}green${NORMAL}')

    If the terminal doesn't support a given action, then the value of
    the corresponding instance variable will be set to ''.  As a
    result, the above code will still work on terminals that do not
    support color, except that their output will not be colored.
    Also, this means that you can test whether the terminal supports a
    given action by simply testing the truth value of the
    corresponding instance variable:

        >>> term = TerminalController()
        >>> if term.CLEAR_SCREEN:
        ...     print 'This terminal supports clearning the screen.'

    Finally, if the width and height of the terminal are known, then
    they will be stored in the `COLS` and `LINES` attributes.
    """
    # Cursor movement:
    BOL = ''             #: Move the cursor to the beginning of the line
    UP = ''              #: Move the cursor up one line
    DOWN = ''            #: Move the cursor down one line
    LEFT = ''            #: Move the cursor left one char
    RIGHT = ''           #: Move the cursor right one char

    # Deletion:
    CLEAR_SCREEN = ''    #: Clear the screen and move to home position
    CLEAR_EOL = ''       #: Clear to the end of the line.
    CLEAR_BOL = ''       #: Clear to the beginning of the line.
    CLEAR_EOS = ''       #: Clear to the end of the screen

    # Output modes:
    BOLD = ''            #: Turn on bold mode
    BLINK = ''           #: Turn on blink mode
    DIM = ''             #: Turn on half-bright mode
    REVERSE = ''         #: Turn on reverse-video mode
    NORMAL = ''          #: Turn off all modes

    # Cursor display:
    HIDE_CURSOR = ''     #: Make the cursor invisible
    SHOW_CURSOR = ''     #: Make the cursor visible

    # Terminal size:
    COLS = None          #: Width of the terminal (None for unknown)
    LINES = None         #: Height of the terminal (None for unknown)

    # Foreground colors:
    BLACK = BLUE = GREEN = CYAN = RED = MAGENTA = YELLOW = WHITE = ''
    
    # Background colors:
    BG_BLACK = BG_BLUE = BG_GREEN = BG_CYAN = ''
    BG_RED = BG_MAGENTA = BG_YELLOW = BG_WHITE = ''
    
    _STRING_CAPABILITIES = """
    BOL=cr UP=cuu1 DOWN=cud1 LEFT=cub1 RIGHT=cuf1
    CLEAR_SCREEN=clear CLEAR_EOL=el CLEAR_BOL=el1 CLEAR_EOS=ed BOLD=bold
    BLINK=blink DIM=dim REVERSE=rev UNDERLINE=smul NORMAL=sgr0
    HIDE_CURSOR=cinvis SHOW_CURSOR=cnorm""".split()
    _COLORS = """BLACK BLUE GREEN CYAN RED MAGENTA YELLOW WHITE""".split()
    _ANSICOLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()

    def __init__(self, term_stream=sys.stdout):
        """
        Create a `TerminalController` and initialize its attributes
        with appropriate values for the current terminal.
        `term_stream` is the stream that will be used for terminal
        output; if this stream is not a tty, then the terminal is
        assumed to be a dumb terminal (i.e., have no capabilities).
        """
        # Curses isn't available on all platforms
        try: import curses
        except: return

        # If the stream isn't a tty, then assume it has no capabilities.
        if not hasattr(term_stream, 'isatty') or not term_stream.isatty(): return

        # Check the terminal type.  If we fail, then assume that the
        # terminal has no capabilities.
        try: curses.setupterm()
        except: return

        # Look up numeric capabilities.
        self.COLS = curses.tigetnum('cols')
        self.LINES = curses.tigetnum('lines')
        
        # Look up string capabilities.
        for capability in self._STRING_CAPABILITIES:
            (attrib, cap_name) = capability.split('=')
            setattr(self, attrib, self._tigetstr(cap_name) or '')

        # Colors
        set_fg = self._tigetstr('setf')
        if set_fg:
            for i,color in zip(range(len(self._COLORS)), self._COLORS):
                setattr(self, color, curses.tparm(set_fg, i) or '')
        set_fg_ansi = self._tigetstr('setaf')
        if set_fg_ansi:
            for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
                setattr(self, color, curses.tparm(set_fg_ansi, i) or '')
        set_bg = self._tigetstr('setb')
        if set_bg:
            for i,color in zip(range(len(self._COLORS)), self._COLORS):
                setattr(self, 'BG_'+color, curses.tparm(set_bg, i) or '')
        set_bg_ansi = self._tigetstr('setab')
        if set_bg_ansi:
            for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
                setattr(self, 'BG_'+color, curses.tparm(set_bg_ansi, i) or '')

    def _tigetstr(self, cap_name):
        # String capabilities can include "delays" of the form "$<2>".
        # For any modern terminal, we should be able to just ignore
        # these, so strip them out.
        import curses
        cap = curses.tigetstr(cap_name) or ''
        return re.sub(r'\$<\d+>[/*]?', '', cap)

    def render(self, template):
        """
        Replace each $-substitutions in the given template string with
        the corresponding terminal control string (if it's defined) or
        '' (if it's not).
        """
        return re.sub(r'\$\$|\${\w+}', self._render_sub, template)

    def _render_sub(self, match):
        s = match.group()
        if s == '$$': return s
        else: return getattr(self, s[2:-1])

    def write(self, stuff):
        sys.stdout.write(stuff)

    def flush(self):
        sys.stdout.flush()

up = 'UP'
down = 'DOWN'
left = 'LEFT'
right = 'RIGHT'
start = 'BOL'
end = 'EOL'

class Terminal(object):
    class InputReader(object):
        _directions = [None, right, left]
        _move_keys = {
            68: -1,
            67: 1
        }
        def __init__(self, terminal, single=False, initial=None):
            self._terminal = terminal
            self._single = single
            self._input = list(initial) if initial is not None else []
            self._fd = sys.stdin.fileno()

        def __enter__(self):
            self._oldterm = termios.tcgetattr(self._fd)
            newattr = termios.tcgetattr(self._fd)
            newattr[3] &= ~termios.ICANON & ~termios.ECHO
            termios.tcsetattr(self._fd, termios.TCSANOW, newattr)
            self._oldflags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
            fcntl.fcntl(self._fd, fcntl.F_SETFL, self._oldflags | os.O_NONBLOCK)
            self._done = False
            self._cursor_position = len(self._input)
            self._terminal.write(''.join(self._input))
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._oldterm)
            fcntl.fcntl(self._fd, fcntl.F_SETFL, self._oldflags)

        @property
        def _char(self):
            return sys.stdin.read(1)

        def read(self):
            while not self._done:
                try:
                    self._handle_input()
                except IOError:
                    sleep(0.01)
            return ''.join(self._input)

        def _handle_input(self):
            char = self._char
            num = ord(char)
            logger.debug('first ordinal: %d' % num)
            if num == 27:
                self._input_movement()
            elif num == 127:
                self._backspace()
            else:
                self._input_content(char)

        def _input_movement(self):
            char2, char3 = ord(self._char), ord(self._char)
            if not self._single:
                logger.debug('second ordinal: %d' % char2)
                logger.debug('third ordinal: %d' % char3)
                if char2 == 91:
                    if char3 == 51:
                        fourth = ord(self._char)
                        if fourth == 126:
                            self._delete()
                        else:
                            logger.debug('fourth ordinal: %d' % fourth)
                    elif char3 == 70:
                        # end
                        self._move_cursor(1, len(self._input) -
                                          self._cursor_position)
                    elif char3 == 72:
                        # home
                        self._move_cursor(-1, self._cursor_position)
                    elif char3 in [50, 53, 54]:
                        fourth = ord(self._char)
                        logger.debug('fourth ordinal: %d' % fourth)
                    elif self._move_keys.has_key(char3):
                        self._move_cursor(self._move_keys[char3])

        def _input_content(self, char):
            self._done = char == '\n' or self._single
            if char != '\n':
                self._input.insert(self._cursor_position, char)
                self._terminal.write(self._right_of_cursor)
                self._terminal.move(left, len(self._input) -
                                    self._cursor_position - 1)
                self._cursor_position += 1

        @property
        def _right_of_cursor(self):
            return ''.join(self._input[self._cursor_position:])

        def _delete(self):
            if not self._single and self._cursor_position < len(self._input):
                del self._input[self._cursor_position]
                self._terminal.write(self._right_of_cursor + ' ')
                self._terminal.move(left, len(self._input) -
                                    self._cursor_position + 1)

        def _backspace(self):
            if not self._single and self._cursor_position > 0:
                self._terminal.move(left)
                self._cursor_position -= 1
                self._delete()

        def _move_cursor(self, value, count=1):
            dist = value * count
            if len(self._input) >= self._cursor_position + dist >= 0:
                dir = self._directions[value]
                self._cursor_position += dist
                self._terminal.move(dir, count)

    terminal_controller = TerminalController()
    _lines = 0
    locked = False
    _cols = terminal_controller.COLS
    _stack = []
    _locks = []
    _has_cols = _cols is not None

    def __init__(self):
        self.unlock()

    def tcap(self, string):
        return getattr(self.terminal_controller, string, '')

    def move(self, direction, count=1):
        string = self.tcap(direction) * count
        self.write(string)

    def hide_cursor(self):
        self.write(self.tcap('HIDE_CURSOR'))

    def show_cursor(self):
        self.write(self.tcap('SHOW_CURSOR'))

    def lock(self):
        Terminal._lines = 0
        Terminal.locked = True
        del Terminal._stack[:]

    def unlock(self):
        Terminal._lines = 0
        Terminal.locked = False
        if Terminal._locks:
            del Terminal._locks[:]

    def push_lock(self):
        if not self.locked:
            self.lock()
        Terminal._locks.append(0)

    def pop_lock(self):
        if Terminal._locks:
            self.pop(Terminal._locks[-1])
            Terminal._locks.pop()
            if not Terminal._locks:
                self.unlock()

    @multimethod(unicode)
    def write(self, string):
        self.write(string.encode('utf-8'))

    @multimethod(str)
    def write(self, string):
        self.terminal_controller.write(string)

    @multimethod(unicode)
    def write_lines(self, data=unicode(''), **kw):
        self.write_lines(data.encode('utf-8'), **kw)

    @multimethod(str)
    def write_lines(self, data='', **kw):
        lines = data.splitlines() if data else ['']
        if len(lines) == 1:
            self.write_line(lines[0], **kw)
        else:
            self.write_lines(lines, **kw)

    @multimethod(list)
    def write_lines(self, data, **kw):
        if any(isinstance(e, LineBreak) for e in data):
            self.write_lines(split_at_linebreak(data))
        elif any(isinstance(e, ColorString) for e in data):
            self.write_color_strings(data)
        else:
            for line in data:
                self.write_lines(line, **kw)

    def write_line(self, data='', check_length=True):
        if self._has_cols and check_length and len(data) > self._cols:
            self.write_lines([data[:self._cols], data[self._cols:]],
                             check_length=check_length)
        else:
            if self.locked:
                Terminal._lines += 1
            self.write('\n' + data)

    def write_color_strings(self, data):
        total_len = sum(map(len, data))
        if self._has_cols and total_len > self._cols:
            self.write_lines(break_color_string_list(data, self._cols),
                             check_length=False)
        else:
            self.write_lines(''.join(map(unicode, data)), check_length=False)

    def clear_line(self):
        """ Delete the current line, but don't move up """
        self.move(start)
        self.write(self.tcap('CLEAR_EOL'))

    def delete_lines(self, num):
        if num > 0:
            self.move(start)
            self.move(up, num - 1)
            self.write(self.tcap('CLEAR_EOS'))
            Terminal._lines -= num
            self.move(up, 1)

    def delete_line(self):
        self.delete_lines(1)

    def clear(self):
        self.delete_lines(self._lines)
        self.lock()

    def __getattr__(self, name):
        if hasattr(self.terminal_controller, name.upper()):
            return getattr(self.terminal_controller, name.upper())
        else:
            raise AttributeError(name)

    def input(self, single=False, initial=None):
        reader = Terminal.InputReader(self, single=single, initial=initial)
        with reader as input:
            return input.read()

    def push(self, data='', **kw):
        old = self._lines
        self.write_lines(data, **kw)
        if Terminal.locked:
            Terminal._stack.append(self._lines - old)
            if Terminal._locks:
                Terminal._locks[-1] += 1

    def pop(self, count=1):
        for i in xrange(count):
            if Terminal._stack:
                self.delete_lines(Terminal._stack.pop())
        if Terminal._locks:
            Terminal._locks[-1] -= count
 
    def flush(self):
        self.terminal_controller.flush()

class ColorString(object):
    """ String with formatting, preserving length. """
    term = TerminalController()

    def __init__(self, strng, format):
        self.string = strng
        self.format = format
        
    def __len__(self):
        return len(self.string)

    def __str__(self):
        return self.format + self.string + self.term.NORMAL

    def __unicode__(self):
        return unicode(self.format) + unicode(self.string) + self.term.NORMAL

    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self.string)

    def ljust(self, *a, **kw):
        return ColorString(self.string.ljust(*a, **kw), self.format)

    def split(self, length):
        return (ColorString(self.string[:length], self.format),
                ColorString(self.string[length:], self.format))

    @multimethod(basestring)
    def __radd__(self, other):
        return [other, self]

    @multimethod(list)
    def __radd__(self, other):
        return list.__add__(other, [self])

class LineBreak(ColorString):
    def __init__(self):
        ColorString.__init__(self, '', '')

def split_string(s, length):
    if isinstance(s, ColorString):
        return s.split(length)
    else:
        return s[:length], s[length:]

def break_color_string_list(data, cols):
    lines = []
    current = ''
    width = 0
    for s in data:
        while width + len(s) > cols:
            prefix, s = split_string(s, cols - width)
            lines.append(current + unicode(prefix))
            current = ''
            width = 0
        current += unicode(s)
        width += len(s)
    lines.append(current)
    return lines

def split_at_linebreak(data):
    lines = [[]]
    for e in data:
        if isinstance(e, LineBreak):
            lines.append([])
        else:
            lines[-1].append(e)
    return lines

def break_blocks(blocks):
    def break_lines(lines, block):
        if sum(map(len, lines[-1])) + len(block) >= terminal.cols:
            lines.extend([[''], [' ']])
        else:
            lines[-1].append(' ')
            lines[-1].append(block)
        return lines
    return reduce(break_lines, blocks, [[]])

terminal = Terminal()
