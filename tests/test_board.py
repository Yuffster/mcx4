import unittest

from mcx4.microcontrollers import Microcontroller
from mcx4.board import Board
from mcx4 import time

import mcx4.exceptions as x


class BoardTestCase(unittest.TestCase):

    def test_sleep(self):
        b = Board()
        mc1 = Microcontroller('mc1')
        mc2 = Microcontroller('mc2')
        b.add(mc1)
        b.add(mc2)
        mc1.compile("""
            slp 1
            mov 100 acc
        """)
        t = time.get()
        # We need this one so the other doesn't advance to the
        # end of its sleep cycle.
        mc2.compile("nop")
        b.step()
        self.assertEqual(t + 1, time.get())
        b.step()  # mov 0 acc
        self.assertEqual(t + 2, time.get())
        b.step()  # slp 1
        self.assertEqual(t + 3, time.get())
        b.step()  # ...zzz...
        self.assertEqual(t + 4, time.get())
        b.step()  # ...zzz...
        self.assertEqual(t + 5, time.get())
        self.assertEqual(0, mc1.acc)
        b.advance()
        self.assertEqual(100, mc1.acc)

    def test_sleep_auto_advance(self):
        b = Board()
        mc1 = Microcontroller('mc1')
        t = time.get()
        b.add(mc1)
        mc1.compile("""
            slp 1
            mov 100 acc
        """)
        t = time.get()
        b.step()  # slp 1
        self.assertEqual(t + 1, time.get())
        b.step()  # ... zzz ...
        self.assertEqual(t + 1001, time.get())
        self.assertEqual(0, mc1.acc)
        b.step()  # mov 100 acc
        self.assertEqual(t + 1002, time.get())
        self.assertEqual(100, mc1.acc)

    def test_step_empty_board(self):
        b = Board()
        b.step()

    def test_simultaneous_io_a(self):
        """
        Writes don't register to reads until next cycle.
        """
        b = Board()
        mc1 = Microcontroller(gpio=1)
        mc2 = Microcontroller(gpio=1)
        b.add(mc1)
        b.add(mc2)
        mc1.compile("mov p0 acc")
        mc2.compile("mov 100 p0")
        mc1.p0.link(mc2.p0)
        b.step()
        self.assertEqual(0, mc1.acc)
        b.step()
        self.assertEqual(100, mc1.acc)

    def test_simultaneous_io_b(self):
        # And the other way...
        # The order matters because if the write happens before the
        # read, everything seems like it's working fine.
        b = Board()
        mc1 = Microcontroller(gpio=1)
        mc2 = Microcontroller(gpio=1)
        mc1.compile("mov p0 acc")
        mc2.compile("mov 100 p0")
        b.add(mc2)
        b.add(mc1)
        mc1.p0.link(mc2.p0)
        b.step()
        # mc1 was reading at the same time as the write, so it got the
        # value at the time the cycle started, which is 0.
        self.assertEqual(0, mc1.acc)
        # mc2.p0 is actually outputting 100 now; it just won't be
        # written to mc1.acc until the next cycle.
        self.assertEqual(100, mc2.p0.output)
        b.step()
        self.assertEqual(100, mc2.p0.output)
        self.assertEqual(100, mc1.acc)
