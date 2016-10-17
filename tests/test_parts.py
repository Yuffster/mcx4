import unittest
import parts
import exceptions as x

class MicrocontrollerTestCase(unittest.TestCase):

    def setUp(self):
        parts.Microcontroller._part_count = 0
        self.mc = parts.Microcontroller(gpio=2, xbus=3)

    def test_get_port_gpio(self):
        p0 = self.mc.get_port('p0')
        p1 = self.mc.get_port('p1')
        self.assertIsInstance(p0, parts.GPIO)
        self.assertIsInstance(p1, parts.GPIO)
        self.assertEqual(self.mc.get_port('p0'), p0)
        self.assertNotEqual(p1, p0)
        with self.assertRaises(x.PortException):
            self.mc.get_port('p2')

    def test_get_port_xbus(self):
        mc = parts.Microcontroller(xbus=3)
        x0 = mc.get_port('x0')
        x1 = mc.get_port('x1')
        x2 = mc.get_port('x2')
        self.assertIsInstance(x0, parts.XBUS)
        self.assertIsInstance(x1, parts.XBUS)
        self.assertIsInstance(x2, parts.XBUS)
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
        self.assertIsInstance(self.mc.p1, parts.GPIO)
        self.assertIsInstance(self.mc.x0, parts.XBUS)
        with self.assertRaises(x.PortException):
            self.mc.x10
        with self.assertRaises(AttributeError):
            self.mc.foobarbizz

    def test_port_linking(self):
        p0 = self.mc.p0
        p1 = self.mc.p1
        x0 = self.mc.x0
        mc2 = parts.Microcontroller(name="mc2", gpio=1)
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

    def test_gpio_read_write(self):
        mc1 = parts.Microcontroller(name="mc1", gpio=1)
        mc2 = parts.Microcontroller(name="mc2", gpio=1)
        mc3 = parts.Microcontroller(name="mc3", gpio=1)
        mc1.p0.link(mc2.p0)
        mc1.p0.write(100)
        mc2.p0.write(50)
        self.assertEqual(100, mc2.p0.read())
        self.assertEqual(50, mc1.p0.read())
        mc1.p0.write(0)
        mc1.p0.link(mc3.p0)
        self.assertEqual(0, mc2.p0.read())
        mc3.p0.write(22)
        self.assertEqual(22, mc2.p0.read())
        self.assertEqual(50, mc3.p0.read())
        mc3.p0.unlink()
        self.assertEqual(0, mc2.p0.read())
        mc3.p0.link(mc1.p0)
        self.assertEqual(22, mc2.p0.read())

    def test_basic_code(self):
        mc1 = parts.Microcontroller(name="mc1", gpio=1)
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

    def test_acc_register(self):
        mc1 = parts.Microcontroller(name='mc1', gpio=1)
        acc = mc1.register('acc')
        self.assertEqual(0, acc.read())
        self.assertEqual(0, mc1.acc)
        mc1.execute('add 1')
        self.assertEqual(1, acc.read())
        self.assertEqual(1, mc1.acc)

    def test_dat_registers(self):
        mc = parts.Microcontroller(name='mc1', dats=1)
        d0 = mc.dat0
        dat = mc.dat
        self.assertEqual(d0, dat)
        self.assertIsInstance(d0, parts.Register)
        d0.write(5)
        self.assertEqual(5, d0.read())
        with self.assertRaises(x.RegisterException):
            mc.register('d1')

    def test_null_register(self):
        mc = parts.Microcontroller()
        n = mc.register('null')
        n.write(100)
        self.assertEqual(0, n.read())

    def test_register_independence(self):
        mc = parts.Microcontroller(name='mc1', dats=3)
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
        mc1 = parts.Microcontroller(name='mc1', dats=1)
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
        cpu = parts.CPU()
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
        mc = parts.Microcontroller(name='mc1', dats=0)
        with self.assertRaises(x.RegisterException):
            mc.execute('mov 1 dat')

    def test_teq(self):
        code = """
          teq acc 2
        + mov 1 acc
        - mov 3 acc
        """
        mc = parts.Microcontroller(name='mc1')
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
        mc = parts.Microcontroller()
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
        mc = parts.Microcontroller()
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
        mc = parts.Microcontroller()
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
        mc1 = parts.Microcontroller(gpio=1)
        mc2 = parts.Microcontroller(gpio=2)
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
        mc = parts.Microcontroller()
        mc.execute(c)
        self.assertEqual(0, mc.acc)

    def test_jump(self):
        code = """
        a:add 1
          teq acc 5
        - jmp a
        """
        mc = parts.Microcontroller()
        mc.execute(code)
        self.assertEqual(5, mc.acc)

        code = """
        a:
          add 1
          teq acc 5
        - jmp a
        """
        mc = parts.Microcontroller()
        mc.execute(code)
        self.assertEqual(5, mc.acc)

    def test_not(self):
        mc = parts.Microcontroller()
        self.assertEqual(0, mc.acc)
        mc.execute("not")
        self.assertEqual(100, mc.acc)
        mc.register('acc').write('-999')
        mc.execute("not")
        self.assertEqual(0, mc.acc)
