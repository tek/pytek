__copyright__ = """ Copyright (c) 2011 Torsten Schmits

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

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from quick_orm.extensions import SessionExtension
from quick_orm.core import Database

class Database(Database):
    def __init__(self, connection_string):
        super(Database, self).__init__(connection_string)
        self.engine = create_engine(connection_string, convert_unicode=True,
                                    encoding='utf-8',
                                    connect_args=dict(check_same_thread=False))
        self.session = scoped_session(sessionmaker(autocommit=False,
                                                   autoflush=False,
                                                   bind=self.engine))
        self.session = SessionExtension.extend(self.session)        

