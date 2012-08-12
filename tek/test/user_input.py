__copyright__ = """ Copyright (c) 2012 Torsten Schmits

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

import unittest

# from tek.user_input import UserInput, input_queue
from tek import debug

class UserInputTest(unittest.TestCase):
    def test(self):
        input_queue.append(['asfd'])
        uinput = UserInput(['prompt:'])
        inp = uinput.read()
        debug(inp)

    def test_urwid(self):
        def inp(key):
            l.body.contents[numpy.random.randint(0, 10)].set_text(key)
            l.pack()
            main.draw_screen()
        import urwid
        import numpy
        l = urwid.ListBox(map(urwid.Text, map(str, xrange(10))))
        l2 = urwid.ListBox([urwid.Text('')])
        widget = urwid.Columns([l, l2],
                               box_columns=[1])
        screen = urwid.raw_display.Screen()
        screen.start(alternate_buffer=False)
        main = urwid.MainLoop(widget, screen=screen, unhandled_input=inp)
        main.run()

if __name__ == '__main__':
    unittest.main()
