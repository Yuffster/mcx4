import unittest

from mcx4.microcontrollers import Microcontroller
from mcx4.interfaces import GPIO, XBUS, Register, Interface

import mcx4.exceptions as x


class InterfaceTestCase(unittest.TestCase):

    def test_port_linking(self):
        mc = Microcontroller(gpio=2, xbus=2)
        p0 = mc.p0
        p1 = mc.p1
        x0 = mc.x0
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
        mc = Microcontroller()
        p0 = mc.p0
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
