__copyright__ = """ Copyright (c) 2006 Edward Loper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import termios, fcntl, sys, os, re
from time import sleep

from dispatch import generic
from dispatch.strategy import Signature

from tek.log import logger

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
        def __init__(self, terminal, single=False):
            self._terminal = terminal
            self._single = single
            self._fd = sys.stdin.fileno()

        def __enter__(self):
            self._oldterm = termios.tcgetattr(self._fd)
            newattr = termios.tcgetattr(self._fd)
            newattr[3] &= ~termios.ICANON & ~termios.ECHO
            termios.tcsetattr(self._fd, termios.TCSANOW, newattr)
            self._oldflags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
            fcntl.fcntl(self._fd, fcntl.F_SETFL, self._oldflags | os.O_NONBLOCK)
            self._done = False
            self._input = []
            self._cursor_position = 0
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

    def __init__(self):
        self.unlock()

    def tcap(self, string):
        return getattr(self.terminal_controller, string, '')

    def move(self, direction, count=1):
        string = self.tcap(direction) * count
        self.write(string)

    def lock(self):
        Terminal._lines = 0
        Terminal.locked = True
        del Terminal._stack[:]

    def unlock(self):
        Terminal._lines = 0
        Terminal.locked = False

    @generic()
    def write(self, string):
        pass

    @write.when(Signature(string=unicode))
    def write_unicode(self, string):
        self.write(string.encode('utf-8'))

    @write.when(Signature(string=str))
    def write_string(self, string):
        self.terminal_controller.write(string)

    @generic()
    def write_lines(self, data='', check_length=True):
        pass

    @write_lines.when(Signature(data=unicode))
    def write_unicode_line(self, data=unicode(''), check_length=True):
        self.write_lines(data.encode('utf-8'), check_length=check_length)

    @write_lines.when(Signature(data=str))
    def write_string_line(self, data='', check_length=True):
        lines = data.split('\n')
        if len(lines) == 1:
            self.write_line(lines[0], check_length=check_length)
        else:
            self.write_lines(lines, check_length=check_length)

    @write_lines.when(Signature(data=list) | Signature(data=tuple))
    def write_seq(self, data, check_length=True):
        if any(isinstance(e, ColorString) for e in data):
            self.write_color_strings(data)
        else:
            for line in data:
                self.write_lines(line, check_length=check_length)

    def write_line(self, data='', check_length=True):
        if check_length and len(data) > self._cols:
            self.write_lines([data[:self._cols], data[self._cols:]],
                             check_length=check_length)
        else:
            if self.locked:
                Terminal._lines += 1
            self.write('\n' + data)

    def write_color_strings(self, data):
        total_len = sum(map(len, data))
        if total_len > self._cols:
            self.write_lines(break_color_string_list(data, self._cols),
                             check_length=False)
        else:
            self.write_lines(''.join(map(unicode, data)), check_length=False)

    def clear_line(self):
        """ Delete the current line, but don't move up """
        self.move(start)
        self.write(self.tcap('CLEAR_EOL'))

    def delete_lines(self, num):
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

    def input(self, single=False):
        with Terminal.InputReader(self, single) as input:
            return input.read()

    def push(self, data=''):
        old = self._lines
        self.write_lines(data)
        if self.locked:
            Terminal._stack.append(self._lines - old)

    def pop(self, count=1):
        if Terminal._stack:
            for i in xrange(count):
                self.delete_lines(Terminal._stack.pop())
 
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

    def ljust(self, *a, **kw):
        return ColorString(self.string.ljust(*a, **kw), self.format)

    def split(self, length):
        return (ColorString(self.string[:length], self.format),
                ColorString(self.string[length:], self.format))

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
            lines.append(current + str(prefix))
            current = ''
            width = 0
        current += str(s)
        width += len(s)
    lines.append(current)
    return lines

terminal = Terminal()
