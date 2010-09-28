__copyright__ = """ Copyright (c) 2009 Torsten Schmits

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

from itertools import imap
from re import compile as regex
from copy import copy

from tek.log import logger
from tek.tools import *
from tek.errors import InternalError, InvalidInput, MooException
from tek.command_line import command_line
from tek.io.terminal import terminal

def is_digit(arg):
    return isinstance(arg, int) or (isinstance(arg, (unicode, str)) and
                                    arg.isdigit())
    
class UserInput(object):
    def __init__(self, text, validator=None, validate=True, newline=True,
                 single=False, remove_text=False):
        self._text = text
        self._validator = validator
        self._do_validate = validate
        self._newline = newline
        self._single = single
        self._remove_text = remove_text
        self.__init_attributes()

    def __init_attributes(self):
        self._input = None
        self._args = None
        self._setup_validator()

    def _setup_validator(self):
        pass

    @property
    def value(self):
        return decode(self._input)

    @property
    def args(self):
        return self._args

    def read(self):
        prompt = self.prompt
        clear_count = max(len(prompt) - len(self.fail_prompt), 0)
        lower = prompt[clear_count:]
        upper = prompt[:clear_count]
        if not terminal.locked:
            terminal.lock()
        terminal.push(upper)
        while not self._read(lower):
            lower = self.fail_prompt
        if self._remove_text:
            terminal.pop()
            terminal.pop()
        if self._newline:
            terminal.write_line()
        return self.value

    def _read(self, prompt):
        terminal.push(prompt)
        terminal.write(' ')
        input = terminal.input(self._single)
        valid = self._do_input(input)
        if not valid:
            terminal.pop()
        return valid

    def input(self, input):
        """ Synthetic input, replacing user interaction """
        terminal.push(self._text)
        if self._do_input(input):
            return self.value
        else:
            raise InvalidInput(input)

    def _do_input(self, input):
        self._input = input
        return self._validate()

    def _validate(self):
        return not (self._do_validate and self._validator and not
                    self._validator.match(str(self._input)))

    @property
    def prompt(self):
        return self._text

    @property
    def fail_prompt(self):
        return ['Invalid input. Try again:']

class SimpleChoice(UserInput):
    def __init__(self, elements, text=[], additional=[], *a, **kw):
        self.text = text
        self._elements = map(str, elements)
        self._additional = map(str, additional)
        UserInput.__init__(self, [], *a, **kw)

    def _setup_validator(self):
        self._validator = regex(r'^(%s)$' % '|'.join(self._elements +
                                               self._additional))

    @property
    def prompt(self):
        text = list(self.text)
        text[-1] += self.input_hint_string
        return text

    @property
    def fail_prompt(self):
        sup = UserInput.fail_prompt.fget(self)
        sup[-1] += self.input_hint_string
        return sup

    @property
    def input_hint_string(self):
        v = filter(None, self.input_hint)
        return ' [%s]' % '/'.join(v) if v else ''

    @property
    def input_hint(self):
        return filter(lambda e: not e.isdigit(), self._elements)

    def add_element(self, e):
        self._elements.append(str(e))
        self._setup_validator()

class SingleCharSimpleChoice(SimpleChoice):
    """ Restrict input to single characters, allowing omission of
    newline for input. Fallback to conventional SimpleChoice if choices
    contain multi-char elements.
    """
    def __init__(self, elements, enter=None, additional=[], validate=True,
                 *args, **kwargs):
        if enter:
            additional += ['']
        self._enter = enter
        single = all(len(str(e)) == 1 for e in elements) and validate
        SimpleChoice.__init__(self, elements, additional=additional,
                              single=single, validate=validate, *args, **kwargs)
        if not single:
            self._do_input = super(SingleCharSimpleChoice, self)._do_input

    def _do_input(self, input):
        return SimpleChoice._do_input(self, self._enter if self._enter and input
                                      == '' else input)

class YesNo(SingleCharSimpleChoice):
    def __init__(self, text=['Confirm'], *args, **kwargs):
        SingleCharSimpleChoice.__init__(self, ['y', 'n'], text=text, enter='y')

    @property
    def value(self):
        return self._input == 'y'

    def __nonzero__(self):
        return self.value

class SpecifiedChoice(SingleCharSimpleChoice):
    """ Automatically supply enumeration for the strings available for
    choice and query for a number.
    """
    def __init__(self, elements, text_pre=None, text_post=None, simple=None,
                 *args, **kwargs):
        self._choices = elements
        self._simple = simple or []
        text_pre = text_pre or []
        text_post = text_post or []
        for i, v in enumerate(self._choices):
            text_pre.append(' [%d] %s' % (i + 1, v))
        text_pre += text_post
        self._numbers = range(1, len(elements) + 1)
        SingleCharSimpleChoice.__init__(self, elements=self._numbers,
                                        text=text_pre, additional=self._simple,
                                        *args, **kwargs)

    @property
    def fail_prompt(self):
        sup = SingleCharSimpleChoice.fail_prompt.fget(self)
        return sup

    @property
    def input_hint(self):
        return self._simple

    def _is_choice_index(self, index):
        return is_digit(index) and 0 < int(index) <= len(self._choices)

    @property
    def value(self):
        i = SingleCharSimpleChoice.value.fget(self)
        if i in self._simple:
            return i
        elif self._is_choice_index(i):
            return self._choices[int(i) - 1]
        elif not self._do_validate:
            return i
        else:
            raise InternalError('SpecifiedChoice: strange input: ' +
                                self._input)

    @property
    def raw_value(self):
        i = SingleCharSimpleChoice.raw_value.fget(self)
        if i in self._simple or self._is_choice_index(i) or not \
           self._do_validate:
            return i
        else:
            raise InternalError('SpecifiedChoice: strange input: ' +
                                self._input)

    @property
    def index(self):
        i = self._input
        return int(i) - 1 if self._is_choice_index(i) else -1

    def add_choice(self, new):
        self._choices.append(new)
        num = len(self._choices)
        self._numbers.append(num)
        self.add_element(num)

class LoopingInput(object):
    def __init__(self, terminate='q', overwrite=False):
        self._terminate = terminate
        self._overwrite = overwrite

    def read(self):
        if self._overwrite:
            self._remove_text = True
        while True:
            value = super(LoopingInput, self).read()
            if value == self._terminate:
                break
            self.process()
        if self._overwrite:
            terminal.write_lines(self.prompt)
            terminal.write_lines()
        return self.loop_value

    def process(self):
        pass
