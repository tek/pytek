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

from re import compile as regex
from tek.errors import InternalError
from tek.command_line import command_line

# TODO make text a list of lines

class UserInput(object):
    def __init__(self, text, validator=None, validate=True):
        self.input = None
        self.text = text
        self.validator = validator
        self.validate = validate

    @property
    def value(self):
        return self.input

    def read(self):
        prompt = self.text + ' '
        if isinstance(prompt, unicode):
            prompt = prompt.encode('utf-8')
        wait = True
        while wait:
            self.input = raw_input(prompt)
            if (not self.validate) or (not self.validator) or \
               self.validator.match(str(self.input)):
                wait = False
            else:
                prompt = "Invalid input. Try again: "
        return self.value

class SimpleChoice(UserInput):
    def __init__(self, elements, text='Choose one'):
        strings = map(str, elements)
        validator = regex(r'^(%s)$' % '|'.join(strings))
        text += ' [' + '/'.join(strings) + ']'
        UserInput.__init__(self, text, validator)

class YesNo(SimpleChoice):
    def __init__(self, text='Confirm'):
        SimpleChoice.__init__(self, ['y', 'n'], text)

    @property
    def value(self):
        return self.input == 'y'

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
            text += '\n [%d] %s' % (k + 1, v)
        text += "\nEnter your choice:"
        validator = regex(r'^(%s)$' % '|'.join(map(str,
                                                   xrange(1, len(elements) + 1))
                                               + additional))
        UserInput.__init__(self, text, validator, *args, **kwargs)

    @property
    def value(self):
        if self.input in self.additional:
            return self.input
        elif self.input.isdigit():
            return self.choices[int(self.input) - 1]
        elif not self.validate:
            return self.input
        else:
            raise InternalError('SpecifiedChoice: strange input: ' + self.input)
