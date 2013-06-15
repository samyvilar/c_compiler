__author__ = 'samyvilar'

from unittest import TestCase
from itertools import izip

from back_end.virtual_machine.cpu.word import bin_repr

from back_end.virtual_machine.cpu.alu import byte_adder, byte_inverter, byte_and, byte_or, byte_xor, z


# byte_adder = build_adder()
# byte_inverter = build_inverter()
# byte_and = build_and()
# byte_or = build_or()
# byte_xor = build_xor()


class TestBitCircuits(TestCase):
    def setUp(self):
        self.tables = {
            'byte_adder': byte_adder,
            'byte_and': byte_and,
            'byte_or': byte_or,
            'byte_xor': byte_xor,
            'byte_inverter': byte_inverter,
        }
        self.operands = izip((0, 10, 128, 255), (-12, 24, 56, -128))

    def test_bit_adder(self):
        table = self.tables['byte_adder']
        for oper1, oper2 in self.operands:
            assert bin_repr(oper1 + oper2) == table[z, bin_repr(oper1), bin_repr(oper2)][1]

    def test_inverter(self):
        table = self.tables['byte_inverter']
        for oper1, _ in self.operands:
            assert bin_repr(~oper1) == table[bin_repr(oper1), ]

    def test_bit_or(self):
        table = self.tables['byte_or']
        for oper1, oper2 in self.operands:
            assert bin_repr(oper1 | oper2) == table[bin_repr(oper1), bin_repr(oper2)]

    def test_bit_and(self):
        table = self.tables['byte_and']
        for oper1, oper2 in self.operands:
            assert bin_repr(oper1 & oper2) == table[bin_repr(oper1), bin_repr(oper2)]

    def test_bit_xor(self):
        table = self.tables['byte_xor']
        for oper1, oper2 in self.operands:
            assert bin_repr(oper1 ^ oper2) == table[bin_repr(oper1), bin_repr(oper2)]