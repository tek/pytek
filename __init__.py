__copyright__ = """ Copyright (c) 2009-2011 Torsten Schmits

This file is part of tek-utils. tek-utils is free software;
you can redistribute it and/or modify it under the terms of the GNU General
Public License version 2, as published by the Free Software Foundation.

tek-utils is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA  02111-1307  USA

"""

from .util.debug import dodebug
from .log import logger, debug
from .process import process, process_output
from .errors import MooException
from .command_line import command_line, PrefixPrinter
from .user_input import YesNo
from .config import Configurations, ConfigClient

try:
    import tek_utils as utils
except ImportError:
    logger.debug('Couldn\'t import tek_utils!')
