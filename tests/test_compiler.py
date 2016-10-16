import unittest
from parts import Microcontroller

import exceptions as x

class CompilerTest(unittest.TestCase):

	def test_ast(self):
		return
		mc = Microcontroller()
		cpu = CPU(mc)
		r1 = mc.register('acc')
		r2 = mc.register('p0')
		cpu.compile('mov acc p0')
		expected = (
			self.do_mov, r1, r2
		)