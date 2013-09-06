__copyright__ = """ Copyright (c) 2009-2011 Torsten Schmits

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

class MooException(Exception):
    def __init__(self, msg=''):
        Exception.__init__(self, str(msg))

class NoOverloadError(NotImplementedError):
    def __init__(self, function, obj):
        error_msg = '%s cannot handle parameters of type %s!' \
                    % (function, type(obj))
        super(NoOverloadError, self).__init__(error_msg)

class InternalError(MooException):
    pass

class InvalidInput(MooException):
    def __init__(self, string):
        super(InvalidInput, self).__init__('Invalid input: %s' % string)

class NotEnoughDiskSpace(MooException):
    def __init__(self, dir, wanted, avail):
        from tek.tools import sizeof_fmt
        text = 'Not enough space in directory "{}" ({} needed, {} available)'
        text = text.format(dir, sizeof_fmt(wanted), sizeof_fmt(avail))
        super(NotEnoughDiskSpace, self).__init__(text)
