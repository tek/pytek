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

from itertools import imap
from re import compile as regex

from tek.tools import *
from tek.errors import InternalError
from tek.command_line import command_line

class UserInput(object):
    def __init__(self, text, validator=None, validate=True, args=False):
        """ @param args bool: allow space separated arguments to the input

        """
        self._text = text
        self._validator = validator
        self._do_validate = validate
        self._allow_args = args
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
        return self. _args

    def read(self):
        prompt = str_list(self._text, j='\n') + ' '
        if isinstance(prompt, unicode):
            prompt = prompt.encode('utf-8')
        while not self._read(prompt):
            prompt = "Invalid input. Try again: "
        return self.value

    def _read(self, prompt):
        return self._do_input(raw_input(prompt))

    def input(self, input):
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

class SimpleChoice(UserInput):
    def __init__(self, elements, text=['Choose one'], additional=[], *args,
                 **kwargs):
        self._elements = map(str, elements)
        self._additional = map(str, additional)
        if self._elements:
            text[-1] += ' [' + '/'.join(self._elements) + ']'
        UserInput.__init__(self, text, *args, **kwargs)

    def _setup_validator(self):
        self._validator = regex(r'^(%s)$' % '|'.join(self._elements +
                                               self._additional))

class YesNo(SimpleChoice):
    def __init__(self, text=['Confirm'], *args, **kwargs):
        SimpleChoice.__init__(self, ['y', 'n'], text)

    @property
    def value(self):
        return self._input == 'y'

    def __nonzero__(self):
        return self.value

class SpecifiedChoice(SimpleChoice):
    """ Automatically supply enumeration for the strings available for
    choice and query for a number. Can additionally take custom strings
    as valid input.

    """
    def __init__(self, elements, text, simple=[], *args, **kwargs):
        self._choices = elements
        self._simple = simple
        for i, v in enumerate(self._choices):
            text.append(' [%d] %s' % (i + 1, v))
        text.append("Enter your choice:")
        #validator = regex(r'^(%s)$' % '|'.join(map(str,
                                                   #xrange(1, len(elements) + 1))
                                               #+ simple))
        elements = range(1, len(elements) + 1)
        SimpleChoice.__init__(self, simple, text, elements, *args, **kwargs)

    @property
    def value(self):
        if self._input in self._simple:
            return self._input
        elif self._input.isdigit() and 0 < int(self._input) <= len(self._choices):
            return self._choices[int(self._input) - 1]
        elif not self._do_validate:
            return self._input
        else:
            raise InternalError('SpecifiedChoice: strange input: ' + self._input)
