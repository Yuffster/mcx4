import unittest
import parts

class MicrocontrollerTestCase(unittest.TestCase):

    def setUp(self):
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
