import unittest

from mcx4.microcontrollers import Microcontroller, MC4000, MC6000
from mcx4.interfaces import GPIO, XBUS, Register, Interface
from mcx4.cpus import CPU
from mcx4.board import Board
from mcx4 import time

import mcx4.exceptions as x

class MicrocontrollerTestCase(unittest.TestCase):

    def setUp(self):
        Microcontroller._part_count = 0
        self.mc = Microcontroller(gpio=2, xbus=3)

    def test_get_port_gpio(self):
        p0 = self.mc.get_port('p0')
        p1 = self.mc.get_port('p1')
        self.assertIsInstance(p0, GPIO)
        self.assertIsInstance(p1, GPIO)
        self.assertEqual(self.mc.get_port('p0'), p0)
        self.assertNotEqual(p1, p0)
        with self.assertRaises(x.PortException):
            self.mc.get_port('p2')

    def test_get_port_xbus(self):
        mc = Microcontroller(xbus=3)
        x0 = mc.get_port('x0')
        x1 = mc.get_port('x1')
        x2 = mc.get_port('x2')
        self.assertIsInstance(x0, XBUS)
        self.assertIsInstance(x1, XBUS)
        self.assertIsInstance(x2, XBUS)
        self.assertEqual(x0, mc.get_port('x0'))
        self.assertEqual(x1, mc.get_port('x1'))
        self.assertEqual(x2, mc.get_port('x2'))
        self.assertNotEqual(x1, x2)
        self.assertNotEqual(x1, x0)
        with self.assertRaises(x.PortException):
            self.mc.get_port('x3')
        self.assertNotEqual(x1, x0)

    def test_get_invalid_port(self):
        bad_ports = ['lawl', 'l0', 'python']
        for p in bad_ports:
            with self.assertRaises(x.PortException):
                self.mc.get_port(p)

    def test_link_nonport(self):
        with self.assertRaises(TypeError):
            self.mc.p0.link(self.mc)

    def test_get_port_shorthand(self):
        self.assertIsInstance(self.mc.p1, GPIO)
        self.assertIsInstance(self.mc.x0, XBUS)
        with self.assertRaises(x.PortException):
            self.mc.x10
        with self.assertRaises(AttributeError):
            self.mc.foobarbizz

    def test_port_linking(self):
        p0 = self.mc.p0
        p1 = self.mc.p1
        x0 = self.mc.x0
        mc2 = Microcontroller(name="mc2", gpio=1)
        p0b = mc2.p0
        with self.assertRaises(x.PortSelfLinkException):
            p0.link(p1)
        with self.assertRaises(x.PortCompatException):
            p0.link(x0)
        p0b.link(p1)
        self.assertEqual(p0b._circuit, p1._circuit)
        p0b.unlink()
        self.assertEqual(p0b._circuit, None)
        p0b.link(p1)
        self.assertEqual(p0b._circuit, p1._circuit)

    def test_reset_gpio_on_read(self):
        p0 = self.mc.p0
        p1 = Microcontroller(gpio=2).p1
        p0.link(p1)
        p0.write(100)
        self.assertEqual(100, p1.read())
        p0.read()
        self.assertEqual(0, p1.read())

    def test_gpio_read_write(self):
        mc1 = Microcontroller(name="mc1", gpio=1)
        mc2 = Microcontroller(name="mc2", gpio=1)
        mc3 = Microcontroller(name="mc3", gpio=1)
        mc1.p0.link(mc2.p0)
        mc1.p0.write(100)
        self.assertEqual(100, mc2.p0.read())
        mc2.p0.write(50)
        self.assertEqual(50, mc1.p0.read())
        mc1.p0.write(0)
        mc1.p0.link(mc3.p0)
        self.assertEqual(0, mc2.p0.read())
        mc2.p0.write(50)
        mc3.p0.write(22)
        self.assertEqual(22, mc2.p0.read())
        mc2.p0.write(50)
        self.assertEqual(50, mc3.p0.read())
        mc3.p0.unlink()
        self.assertEqual(0, mc2.p0.read())
        mc3.p0.link(mc1.p0)
        mc3.p0.write(22)
        self.assertEqual(22, mc2.p0.read())

    def test_add_and_sub(self):
        mc1 = Microcontroller(name="mc1", gpio=1)
        mc1.execute('add 1')
        self.assertEqual(1, mc1.acc)
        mc1.execute('add 1')
        self.assertEqual(2, mc1.acc)
        mc1.execute('sub 1')
        self.assertEqual(1, mc1.acc)
        mc1.execute('#sub 1')
        self.assertEqual(1, mc1.acc)
        with self.assertRaises(x.CommandException):
            mc1.execute('lawl')

    def test_mul(self):
        mc = Microcontroller()
        mc.register('acc').write(2)
        mc.execute('mul 5')
        self.assertEqual(10, mc.acc)

    def test_not(self):
        mc = Microcontroller()
        self.assertEqual(0, mc.acc)
        mc.execute("not")
        self.assertEqual(100, mc.acc)
        mc.register('acc').write('-999')
        mc.execute("not")
        self.assertEqual(0, mc.acc)

    def test_dgt(self):
        mc = Microcontroller()
        mc.register('acc').write(567)
        mc.execute('dgt 0')
        self.assertEqual(7, mc.acc)
        mc.register('acc').write(567)
        mc.execute('dgt 1')
        self.assertEqual(6, mc.acc)
        mc.register('acc').write(567)
        mc.execute('dgt 2')
        self.assertEqual(5, mc.acc)
        mc.register('acc').write(567)
        mc.execute('dgt 3')
        self.assertEqual(0, mc.acc)

    def test_dst(self):
        mc = Microcontroller()
        mc.register('acc').write(567)
        mc.execute('dst 0 9')
        self.assertEqual(569, mc.acc)
        mc.register('acc').write(567)
        mc.execute('dst 1 9')
        self.assertEqual(597, mc.acc)
        mc.register('acc').write(567)
        mc.execute('dst 2 9')
        self.assertEqual(967, mc.acc)
        mc.register('acc').write(567)
        mc.execute('dst 3 9')
        self.assertEqual(0, mc.acc)

    def test_nop(self):
        mc = Microcontroller()
        mc.execute("nop")

    def test_acc_register(self):
        mc1 = Microcontroller(name='mc1', gpio=1)
        acc = mc1.register('acc')
        self.assertEqual(0, acc.read())
        self.assertEqual(0, mc1.acc)
        mc1.execute('add 1')
        self.assertEqual(1, acc.read())
        self.assertEqual(1, mc1.acc)

    def test_dat_registers(self):
        mc = Microcontroller(name='mc1', dats=1)
        d0 = mc.dat0
        dat = mc.dat
        self.assertEqual(d0, dat)
        self.assertIsInstance(d0, Register)
        d0.write(5)
        self.assertEqual(5, d0.read())
        with self.assertRaises(x.RegisterException):
            mc.register('d1')

    def test_null_register(self):
        mc = Microcontroller()
        n = mc.register('null')
        n.write(100)
        self.assertEqual(0, n.read())

    def test_register_independence(self):
        mc = Microcontroller(name='mc1', dats=3)
        d0 = mc.dat0
        d1 = mc.dat1
        d2 = mc.dat2
        d0.write(5)
        d1.write(6)
        d2.write(7)
        self.assertEqual(5, d0.read())
        self.assertEqual(6, d1.read())
        self.assertEqual(7, d2.read())
        d0.inc()
        d1.inc()
        d2.inc()
        self.assertEqual(6, d0.read())
        self.assertEqual(7, d1.read())
        self.assertEqual(8, d2.read())

    def test_mov(self):
        mc1 = Microcontroller(name='mc1', dats=1)
        acc = mc1.register('acc')
        dat = mc1.register('dat')
        acc.write(42)
        mc1.execute('mov acc dat')
        self.assertEqual(42, dat.read())
        self.assertEqual(42, acc.read())
        dat.write(12)
        mc1.execute('mov dat acc')
        self.assertEqual(12, acc.read())
        self.assertEqual(12, dat.read())

    def test_compiler(self):
        expected = [
            ('mov', '1', 'acc'),
            ('test', 'eq', ('acc', '1')),
            ('cond', True, ('mov', '2', 'acc')),
            ('cond', False, ('mov', '0', 'acc')),
            ('cond', True, ('mov', '1', 'dat')),
            ('mov', 'dat', 'acc')
        ]
        cpu = CPU()
        result = cpu.compile("""
          mov 1 acc     # Comments don't matter.
          teq acc 1     ; I'll add semicolons, too.
        + mov 2 acc     ; You know, just for fun.
        - mov 0 acc
        + mov 1 dat
          mov dat acc
        """)
        self.assertEqual(expected, result)

    def test_execute_bad_register(self):
        mc = Microcontroller(name='mc1', dats=0)
        with self.assertRaises(x.RegisterException):
            mc.execute('mov 1 dat')

    def test_teq(self):
        code = """
          teq acc 2
        + mov 1 acc
        - mov 3 acc
        """
        mc = Microcontroller(name='mc1')
        mc.execute(code)
        self.assertEqual(3, mc.acc)
        mc.register('acc').write(2)
        self.assertEqual(2, mc.acc)
        mc.execute(code)
        self.assertEqual(1, mc.acc)

    def test_tcp(self):
        code = """
          tcp acc 2
        + mov 1 acc
        - mov 3 acc
        """
        mc = Microcontroller()
        mc.execute(code)
        self.assertEqual(3, mc.acc)
        mc.register('acc').write(3)
        mc.execute(code)
        self.assertEqual(1, mc.acc)
        mc.execute(code)
        self.assertEqual(3, mc.acc)
        mc.register('acc').write(2)
        mc.execute(code)
        self.assertEqual(2, mc.acc)

    def test_tlt(self):
        code = """
          tlt acc 2
        + mov 1 acc
        - mov 3 acc
        """
        mc = Microcontroller()
        mc.execute(code)
        self.assertEqual(1, mc.acc)
        mc.register('acc').write(2)
        mc.execute(code)
        self.assertEqual(3, mc.acc)

    def test_tgt(self):
        code = """
          tgt acc 2
        + mov 3 acc
        - mov 1 acc
        """
        mc = Microcontroller()
        mc.execute(code)
        self.assertEqual(1, mc.acc)
        mc.register('acc').write(2)
        mc.execute(code)
        self.assertEqual(1, mc.acc)

    def test_mov_to_port(self):
        c1 = """
          mov 10 p0
        """
        c2 = """
          add p1
        """
        mc1 = Microcontroller(gpio=1)
        mc2 = Microcontroller(gpio=2)
        mc1.p0.link(mc2.p1)
        mc1.execute(c1)
        mc2.execute(c2)
        self.assertEqual(10, mc2.acc)
        mc2.execute(c2)
        self.assertEqual(20, mc2.acc)

    def test_mov_to_null(self):
        c = """
          mov 100 null
          mov 50 acc
          mov null acc
        """
        mc = Microcontroller()
        mc.execute(c)
        self.assertEqual(0, mc.acc)

    def test_jump(self):
        code = """
        a:add 1
          teq acc 5
        - jmp a
        """
        mc = Microcontroller()
        mc.execute(code)
        self.assertEqual(5, mc.acc)

        code = """
        a:
          add 1
          teq acc 5
        - jmp a
        """
        mc = Microcontroller()
        mc.execute(code)
        self.assertEqual(5, mc.acc)

    def test_io_stepping(self):
        mc1 = Microcontroller('mc1', gpio=1)
        mc1.compile("""
            mov p0 acc
        """)
        mc2 = Microcontroller('mc2', gpio=2)
        mc2.compile("""
            mov 1 p1
        """)
        mc1.p0.link(mc2.p1)
        mc2.step()
        mc1.step()
        self.assertEqual(1, mc1.acc)

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
        # We need this one so the other doesn't advance to the end of its sleep
        # cycle.
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

    def test_doc_examples(self):
        mc1 = MC4000()
        mc2 = MC6000()

        mc1.p0.link(mc2.p1)  # Link the ports.
        self.assertEqual(0, mc1.p0.read())
        self.assertEqual(0, mc2.p1.read())

        mc1.p0.write(100)
        self.assertEqual(100, mc2.p1.read())

        mc1 = MC4000()
        mc2 = MC6000()

        mc1.p0.link(mc2.p1)  # Link the ports.
        self.assertEqual(0, mc1.p0.read())
        self.assertEqual(0, mc2.p1.read())

        mc1.p0.write(100)
        self.assertEqual(0, mc1.p0.read())
        self.assertEqual(0, mc2.p1.read())
