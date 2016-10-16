import unittest
import parts

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
        with self.assertRaises(parts.PortException):
            self.mc.get_port('p2')

    def test_get_port_xbus(self):
        x0 = self.mc.get_port('x0')
        x1 = self.mc.get_port('x1')
        x2 = self.mc.get_port('x2')
        self.assertIsInstance(x0, parts.XBUS)
        self.assertIsInstance(x1, parts.XBUS)
        self.assertIsInstance(x2, parts.XBUS)
        self.assertEqual(x0, self.mc.get_port('x0'))
        self.assertEqual(x1, self.mc.get_port('x1'))
        self.assertEqual(x2, self.mc.get_port('x2'))
        self.assertNotEqual(x1, x2)
        self.assertNotEqual(x1, x0)
        with self.assertRaises(parts.PortException):
            self.mc.get_port('x3')
        self.assertNotEqual(x1, x0)

    def test_get_invalid_port(self):
        bad_ports = ['lawl', 'l0', 'python']
        for p in bad_ports:
            with self.assertRaises(parts.PortException):
                self.mc.get_port(p)

    def test_link_nonport(self):
        with self.assertRaises(TypeError):
            self.mc.p0.link(self.mc)

    def test_get_port_shorthand(self):
        self.assertIsInstance(self.mc.p1, parts.GPIO)
        self.assertIsInstance(self.mc.x0, parts.XBUS)
        with self.assertRaises(parts.PortException):
            self.mc.x10
        with self.assertRaises(AttributeError):
            self.mc.foobarbizz

    def test_port_linking(self):
        p0 = self.mc.p0
        p1 = self.mc.p1
        x0 = self.mc.x0
        mc2 = parts.Microcontroller(name="mc2", gpio=1)
        p0b = mc2.p0
        with self.assertRaises(parts.PortSelfLinkException):
            p0.link(p1)
        with self.assertRaises(parts.PortCompatException):
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
