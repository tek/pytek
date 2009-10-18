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
        self._validate = validate
        self._allow_args = args
        self.__init_attributes()

    def __init_attributes(self):
        self._input = None
        self._args = None

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
        while self._read(prompt):
            prompt = "Invalid input. Try again: "
        return self.value

    def _read(self, prompt):
            self._input = raw_input(prompt)
            return self._validate and self._validator and not \
                   self._validator.match(str(self._input))

class SimpleChoice(UserInput):
    def __init__(self, elements, text=['Choose one'], *args, **kwargs):
        strings = map(str, elements)
        validator = regex(r'^(%s)$' % '|'.join(strings))
        text[-1] += ' [' + '/'.join(strings) + ']'
        UserInput.__init__(self, text, validator)

class YesNo(SimpleChoice):
    def __init__(self, text=['Confirm'], *args, **kwargs):
        SimpleChoice.__init__(self, ['y', 'n'], text)

    @property
    def value(self):
        return self._input == 'y'

    def __nonzero__(self):
        return self.value

class SpecifiedChoice(UserInput):
    """ Automatically supply enumeration for the strings available for
    choice and query for a number. Can additionally take custom strings
    as valid input.

    """
    def __init__(self, elements, text, additional=[], *args, **kwargs):
        self.choices = dict(enumerate(elements))
        self.additional = additional
        for k, v in self.choices.iteritems():
            text.append(' [%d] %s' % (k + 1, v))
        text.append("Enter your choice:")
        validator = regex(r'^(%s)$' % '|'.join(map(str,
                                                   xrange(1, len(elements) + 1))
                                               + additional))
        UserInput.__init__(self, text, validator, *args, **kwargs)

    @property
    def value(self):
        if self._input in self.additional:
            return self._input
        elif self._input.isdigit():
            return self.choices[int(self._input) - 1]
        elif not self._validate:
            return self._input
        else:
            raise InternalError('SpecifiedChoice: strange input: ' + self._input)
