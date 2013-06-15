__author__ = 'samyvilar'

from itertools import izip_longest, izip, imap
from struct import pack, unpack
from collections import Iterable

from back_end.virtual_machine.cpu.alu import z, o
from back_end.virtual_machine.cpu.alu import adder, inverter, join_bits, msb, byte_seq
from back_end.virtual_machine.cpu.alu import and_circuit, or_circuit, xor_circuit, bits
from back_end.virtual_machine.cpu.alu import shift_left, shift_right, multiplier, divider


def int_to_bin(number, bit_size=8):
    number %= 2**bit_size
    if number == 0:
        return str(z) * bit_size
    return str(z) * (bit_size - number.bit_length()) + bin(number)[2:]


def float_to_bin(number, bit_size=8):
    return ''.join(imap(int_to_bin, imap(ord, pack(Float.fmt, number))))


def bin_repr(number, bit_size=8):
    if isinstance(number, float):
        return float_to_bin(number, bit_size)
    return int_to_bin(number, bit_size)


def twos_complement(word):
    return ~word + Word(1)


class Word(tuple):
    bit_size = 64

    # noinspection PyInitNewSignature
    def __new__(cls, number_or_byte_seq=0):
        if isinstance(number_or_byte_seq, Iterable):
            return super(Word, cls).__new__(cls, number_or_byte_seq)

        bit_repr = bin_repr(number_or_byte_seq, Word.bit_size)
        value = super(Word, cls).__new__(cls, byte_seq(bit_repr))
        value.str = bit_repr
        value.int = int(value)
        value.float = float(number_or_byte_seq)
        return value

    def __add__(self, other):
        assert type(other) is Word
        result, carry = adder(self, other)
        value = Word(result)
        value.carry = result == o
        value.overflow = msb(value) != msb(self) == msb(other)
        return value

    def __sub__(self, other):
        assert type(other) is Word
        return self.__add__(twos_complement(other))

    def __mul__(self, other):
        assert type(other) is Word
        str_result = multiplier(self, other, twos_complement, Word(0), Word(1))
        value = Word(byte_seq(str_result))
        value.str = str_result
        return value

    def __div__(self, other):
        assert type(other) is Word
        quotient, remainder = divider(self, other, twos_complement, Word(0), Word(1))
        return quotient

    def __mod__(self, other):
        quotient, remainder = divider(self, other, twos_complement, Word(0), Word(1))
        return remainder

    def __and__(self, other):
        return Word(and_circuit(self, other))

    def __or__(self, other):
        return Word(or_circuit(self, other))

    def __xor__(self, other):
        return Word(xor_circuit(self, other))

    def __invert__(self):
        return Word(inverter(self))

    def __lshift__(self, other):
        str_result = shift_left(self, other)
        result = Word(byte_seq(str_result))
        result.str = str_result
        return result

    def __rshift__(self, other):
        str_result = shift_right(self, other)
        result = Word(byte_seq(str_result))
        result.str = str_result
        return result

    def __eq__(self, other):
        return int(self) == int(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        if hasattr(self, 'zero'):
            return not self.zero
        self.zero = all(bit == z for bit in bits(self))
        return not self.zero

    def __int__(self):
        if hasattr(self, 'int'):
            return self.int
        if msb(self) == o:  # msb is a one do twos complement and multiply by negative value.
            self.int = -1 * int(str(twos_complement(self)), 2)
        else:
            self.int = int(str(self), 2)
        return self.int

    def __hash__(self):
        return int(self)

    def __float__(self):
        if hasattr(self, 'float'):
            return self.float
        self.float = float(int(self))
        return self.float

    def __str__(self):
        if hasattr(self, 'str'):
            return self.str
        self.str = join_bits(bit for byte in reversed(self) for bit in byte)
        return self.str


class Float(Word):
    fmt = '<d'

    def __add__(self, other):
        assert isinstance(other, Float)
        return Float(float(self) + float(other))

    def __sub__(self, other):
        assert isinstance(other, Float)
        return Float(float(self) - float(other))

    def __mul__(self, other):
        assert isinstance(other, Float)
        return Float(float(self) * float(other))

    def __div__(self, other):
        assert isinstance(other, Float)
        return Float(float(self) / float(other))

    def __int__(self):
        return int(float(self))

    def __float__(self):
        if hasattr(self, 'float'):
            return self.float
        self.float = unpack(Float.fmt, ''.join(imap(chr, imap(lambda v: int(v, 2), reversed(self)))))[0]
        return self.float

    def __eq__(self, other):
        return float(self) == float(other)