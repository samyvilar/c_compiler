__author__ = 'samyvilar'

from unittest import TestCase
from itertools import izip, imap
from random import getrandbits

from back_end.virtual_machine.cpu.word import Word, Float


def random_iter(bit_size, count):
    while count:
        yield getrandbits(bit_size)
        count -= 1


class TestWord(TestCase):
    def setUp(self):
        self.word_type = Word
        input_mag = (Word.bit_size - 1, 10)
        self.values = izip(random_iter(*input_mag), random_iter(*input_mag))

    def evaluate(self, oper1, oper2, func):
        result = getattr(self.word_type, func)(self.word_type(oper1), self.word_type(oper2))
        exp_result = Word(getattr(type(oper1), func)(oper1, oper2))
        self.assertEqual(result, exp_result, '{res} {exp_result}'.format(
            res=int(result), exp_result=int(exp_result))
        )

    def test_addition(self):
        for oper1, oper2 in self.values:
            self.evaluate(oper1, oper2, '__add__')

    def test_subtraction(self):
        for oper1, oper2 in self.values:
            self.evaluate(oper1, oper2, '__sub__')

    def test_multiplication(self):
        for oper1, oper2 in self.values:
            self.evaluate(oper1, oper2, '__mul__')

    # Python doesn't truncate ints after division like C or most hardware implementations.
    # instead it uses floor which rounds off toward 0 which differs from trunc in the neg range.
    # >>> floor(1.9)
    # 1.0
    # >>> floor(-1.9)
    # -2.0
    # >>>
    def test_division(self):
        for oper1, oper2 in self.values:
            result = Word(oper1) / Word(oper2)
            self.assertEqual(result, Word(int(oper1 / float(oper2))))

    def test_mod(self):
        def mod(oper1, oper2):  # Since pythons int division uses floor its mod operator differs from most hardware.
            return oper1 - oper2*int(oper1/float(oper2))

        for oper1, oper2 in self.values:
            self.assertEqual(
                Word(oper1) % Word(oper2), Word(mod(oper1, oper2)),
                '{oper1} % {oper2} = {r} != {a}'.format(
                    oper1=oper1, oper2=oper2, r=int(Word(oper1) % Word(oper2)), a=oper1 % oper2,
                )
            )

    def test_and(self):
        for oper1, oper2 in self.values:
            self.evaluate(oper1, oper2, '__and__')

    def test_or(self):
        for oper1, oper2 in self.values:
            self.evaluate(oper1, oper2, '__or__')

    def test_xor(self):
        for oper1, oper2 in self.values:
            self.evaluate(oper1, oper2, '__xor__')

    def test_inverter(self):
        for oper1, oper2 in self.values:
            self.assertEqual(~Word(oper1), Word(~oper1))
            self.assertEqual(~Word(oper2), Word(~oper2))

    def test_shift_left(self):
        for oper1, oper2 in self.values:
            self.assertEqual(Word(oper1) << Word(oper2), Word(oper1 << (oper2 & (Word.bit_size - 1))))

    def test_shift_right(self):
        for oper1, oper2 in self.values:
            self.assertEqual(Word(oper1) >> Word(oper2), Word(oper1 >> (oper2 & (Word.bit_size - 1))))


class TestFloat(TestCase):
    def setUp(self):
        input_mag = (Word.bit_size/2, 100)
        fraction = lambda value: 1.0/value
        self.values = izip(
            imap(sum, izip(random_iter(*input_mag), imap(fraction, random_iter(*input_mag)))),  # oper1
            imap(sum, izip(random_iter(*input_mag), imap(fraction, random_iter(*input_mag)))),  # oper2
        )

    def test_addition(self):
        for oper1, oper2 in self.values:
            self.assertEqual(Float(oper1) + Float(oper2), Word(oper1 + oper2))

    def test_subtraction(self):
        for oper1, oper2 in self.values:
            self.assertEqual(Float(oper1) - Float(oper2), Word(oper1 - oper2))

    def test_multiplication(self):
        for oper1, oper2 in self.values:
            self.assertEqual(Float(oper1) * Float(oper2), Word(oper1 * oper2))

    def test_division(self):
        for oper1, oper2 in self.values:
            self.assertEqual(Float(oper1) / Float(oper2), Word(oper1 / oper2))