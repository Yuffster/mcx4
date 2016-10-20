import unittest

from mcx4.microcontrollers import Microcontroller, MC4000, MC6000
from mcx4.interfaces import GPIO, XBUS, Register, Interface

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
