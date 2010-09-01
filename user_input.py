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

from tek.log import logger
from tek.tools import *
from tek.errors import InternalError, InvalidInput, MooException
from tek.command_line import command_line
from tek.terminal import terminal

def is_digit(arg):
    return isinstance(arg, int) or (isinstance(arg, str) and arg.isdigit())
    
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
        return self._input

    @property
    def args(self):
        return self._args

    def read(self):
        clear = max(len(self.prompt) - len(self.fail_prompt), 0)
        prompt = self.prompt[clear:]
        if not terminal.locked:
            terminal.lock()
        terminal.push(self.prompt[:clear])
        while not self._read(prompt):
            prompt = self.fail_prompt
        if self._remove_text:
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
        return ['Enter something important:']

    @property
    def fail_prompt(self):
        return ['Invalid input. Try again:']

class SimpleChoice(UserInput):
    def __init__(self, elements, text, additional=[], *a, **kw):
        if isinstance(text, str):
            text = [text]
        self._elements = map(str, elements)
        self._additional = map(str, additional)
        if self._elements:
            text[-1] += ' [' + '/'.join(self._elements) + ']'
        UserInput.__init__(self, text, *a, **kw)

    def _setup_validator(self):
        self._validator = regex(r'^(%s)$' % '|'.join(self._elements +
                                               self._additional))

    @property
    def prompt(self):
        # TODO filter numbers?
        return self._text

    @property
    def fail_prompt(self):
        sup = UserInput.fail_prompt.fget(self)
        # replace by property valid_inputs
        sup[-1] += ' [%s]' % '/'.join(self._elements)
        return sup

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
                                      == '\n' else input)

    #@property
    #def prompt(self):
        #pass

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
    def __init__(self, elements, text, simple=[], *args, **kwargs):
        self._choices = elements
        self._simple = simple
        for i, v in enumerate(self._choices):
            text.append(' [%d] %s' % (i + 1, v))
        text.append("Enter your choice:")
        elements = range(1, len(elements) + 1)
        SingleCharSimpleChoice.__init__(self, elements=elements, text=text,
                                        additional=simple, *args, **kwargs)

    @property
    def prompt(self):
        sup = SingleCharSimpleChoice.prompt.fget(self)
        return sup

    @property
    def fail_prompt(self):
        sup = SingleCharSimpleChoice.fail_prompt.fget(self)
        return sup

    @property
    def valid_inputs(self):
        # TODO not the numbers for choices
        return self._simple


    def _is_choice_index(self, index):
        return is_digit(index) and 0 < int(index) <= len(self._choices)

    @property
    def value(self):
        i = self._input
        if i in self._simple:
            return i
        elif self._is_choice_index(i):
            return self._choices[int(i) - 1]
        elif not self._do_validate:
            return i
        else:
            raise InternalError('SpecifiedChoice: strange input: ' + self._input)

    @property
    def raw_value(self):
        i = self._input
        if i in self._simple or self._is_choice_index(i) or not \
           self._do_validate:
            return i
        else:
            raise InternalError('SpecifiedChoice: strange input: ' + self._input)
