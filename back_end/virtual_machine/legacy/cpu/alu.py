__author__ = 'samyvilar'

import os
from collections import defaultdict
from itertools import product, imap, izip, tee, izip_longest
import cPickle

bit_type = str
bits = str  # return sequence of 0 and 1s big endian (00000100 == 4)
empty_bit = bit_type()
join_bits = empty_bit.join

bit_values = '01'
z, o = bit_values


# Single bit addition table, carry_in , oper1, oper2 = result, carry_out
single_bit_adder = {
    (z, z, z): (z, z),
    (z, z, o): (o, z),
    (z, o, z): (o, z),
    (z, o, o): (z, o),

    (o, z, z): (o, z),
    (o, z, o): (z, o),
    (o, o, z): (z, o),
    (o, o, o): (o, o),
}

single_bit_inverter = {
    (z,): o,
    (o,): z,
}

single_bit_or = {
    (z, z): z,
    (z, o): o,
    (o, z): o,
    (o, o): o,
}

single_bit_and = {
    (z, z): z,
    (z, o): z,
    (o, z): z,
    (o, o): o,
}

single_bit_xor = {
    (z, z): z,
    (z, o): o,
    (o, z): o,
    (o, o): z,
}


def lsb(word):
    return bits(word)[-1]


def msb(word):
    return bits(word)[0]


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)


def byte_seq(bit_repr):  # byte sequence little endian.
    return reversed(map(join_bits, grouper(bit_repr, 8, 0)))


def binary_perm(size):
    return imap(join_bits, product(bit_values, repeat=size))


def input_permutation(input_bit_size):
    return product(binary_perm(input_bit_size), binary_perm(input_bit_size))


input_sequence = izip


class Circuit(defaultdict):
    def __init__(self, default_factory=bit_type, initial_values=None):
        super(Circuit, self).__init__(default_factory=default_factory)
        self.update(initial_values or {})


def build_adder(size=8, single_bit_adder=single_bit_adder):
    table = Circuit(initial_values={z: Circuit(), o: Circuit()})
    for carry_in in bit_values:
        for input_1, input_2 in input_permutation(size):
            val, carry = empty_bit, carry_in
            for bit_0, bit_1 in input_sequence(reversed(input_1), reversed(input_2)):
                v, carry = single_bit_adder[carry, bit_0, bit_1]
                val += v
            table[carry_in, input_1, input_2] = carry,  join_bits(reversed(val))
    return table


def build_bit_circuit(size, single_bit_func):
    table = Circuit()
    for input_1, input_2 in input_permutation(size):
        table[(input_1, input_2)] = join_bits(
            single_bit_func[bit_0, bit_1] for bit_0, bit_1 in input_sequence(input_1, input_2)
        )
    return table


def build_or(size=8, single_bit_or=single_bit_or):
    return build_bit_circuit(size, single_bit_or)


def build_and(size=8, single_bit_and=single_bit_and):
    return build_bit_circuit(size, single_bit_and)


def build_xor(size=8, single_bit_xor=single_bit_xor):
    return build_bit_circuit(size, single_bit_xor)


def build_inverter(size=8, single_bit_inverter=single_bit_inverter):
    return Circuit(initial_values={
        (byte,): join_bits(single_bit_inverter[bit, ] for bit in byte) for byte in binary_perm(size)
    })


# cache the circuits to reduce VM start up and test time.
def get_cached_circuit(circuit_file, circuit_func, cached_circuits_path='back_end/virtual_machine/cpu/circuits', cache=True):
    file_path = os.path.join(os.getcwd(), cached_circuits_path, circuit_file)
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as cached_file:
            obj = cPickle.load(cached_file)
    else:
        obj = circuit_func()
        if cache and os.path.isdir(os.path.dirname(file_path)):
            with open(file_path, 'wb') as caching_file:
                cPickle.dump(obj, caching_file, cPickle.HIGHEST_PROTOCOL)
    return obj


# byte_adder = get_cached_circuit('byte_adder.p', build_adder)  # File quite large.
# byte_and = get_cached_circuit('byte_and.p', build_and)
# byte_or = get_cached_circuit('byte_or.p', build_or)
# byte_xor = get_cached_circuit('byte_xor.p', build_xor)
# byte_inverter = get_cached_circuit('byte_inverter.p', build_inverter)


class CacheCircuit(dict):
    def __init__(self, impl):
        self.impl = impl
        super(CacheCircuit, self).__init__()

    def __getitem__(self, item):
        if item not in self:
            self[item] = join_bits(self.impl[inputs] for inputs in input_sequence(*item))
        return super(CacheCircuit, self).__getitem__(item)

byte_and = CacheCircuit(single_bit_and)
byte_or = CacheCircuit(single_bit_or)
byte_xor = CacheCircuit(single_bit_xor)
byte_inverter = CacheCircuit(single_bit_inverter)


class ByteAdder(CacheCircuit):
    def __getitem__(self, item):
        if item not in self:
            values = []
            carry, input_0, input_1 = item
            for bit_0, bit_1 in input_sequence(reversed(input_0), reversed(input_1)):
                val, carry = self.impl[carry, bit_0, bit_1]
                values.append(val)
            self[item] = carry, join_bits(reversed(values))
        return super(ByteAdder, self).__getitem__(item)

byte_adder = ByteAdder(single_bit_adder)


def pad_right(value, symbol, size):
    return value + (symbol * (size - len(value)))


def pad_left(value, symbol, size):
    return (symbol * (size - len(value))) + value


def adder(word_1, word_2, byte_adder=byte_adder):
    result, carry = [], z
    for byte_1, byte_2 in input_sequence(word_1, word_2):
        carry, r = byte_adder[carry, byte_1, byte_2]
        result.append(r)
    return result, carry


def pairwise(iterable):  # "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def calc_transitions(bit_array):
    return sum(bit_0 != bit_1 for bit_0, bit_1 in pairwise(bit_array))


def multiplier(word_1, word_2, twos_complement, zero, one):  # Booths algorithm ...
    if not word_1 or not word_2:  # If either is zero just return 0.
        return word_1 and word_2
    factor, multiplicand = min((word_1, word_2), (word_2, word_1), key=lambda pair: calc_transitions(bits(pair[0])))
    negative_multiplicand, result, overflow = twos_complement(multiplicand), zero, empty_bit
    for previous_lsb, current_lsb in pairwise(reversed(bits(factor) + z)):
        result = multiplier.rules[current_lsb, previous_lsb](result, multiplicand, negative_multiplicand)
        overflow += lsb(result)
        result >>= one
    return join_bits(reversed(overflow))
multiplier.rules = {
    (z, z): lambda result, multiplicand, negative_multiplicand: result,
    (o, o): lambda result, multiplicand, negative_multiplicand: result,
    (o, z): lambda result, multiplicand, negative_multiplicand: negative_multiplicand + result,
    (z, o): lambda result, multiplicand, negative_multiplicand: multiplicand + result,
}


def divider(oper1, oper2, twos_complement, zero, one):
    if not oper2:  # Division by zero raises an exception, halting the vm.
        raise ZeroDivisionError
    if not oper1:  # zero divided by any value is zero, with a remainder of zero.
        return zero, zero
    # At this point neither operand should be 0.

    dividend = (msb(oper1) == o and twos_complement(oper1)) or oper1
    divisor = (msb(oper2) == o and twos_complement(oper2)) or oper2
    quotient = zero

    msb_displacement = (len(bits(dividend)) - bits(dividend).index(o)) - (len(bits(divisor)) - bits(divisor).index(o))

    if msb_displacement < 0:  # divisor greater than numerator, answer is 0
        return zero, oper1

    base_index = one << msb_displacement
    divisor <<= msb_displacement  # align dividend and divisors most significant 1.

    msb_displacement += 1  # account for zeroth location.
    while msb_displacement:
        diff = dividend - divisor
        if msb(diff) == z:  # positive result.
            dividend = diff
            quotient += base_index
        divisor >>= one
        base_index >>= one
        msb_displacement -= 1

    # Set the sign of the quotient and remainder depending on operand1 and operand2 sign
    return (msb(oper1) != msb(oper2) and twos_complement(quotient)) or quotient, \
           (msb(oper1) != msb(dividend) and twos_complement(dividend)) or dividend


def and_circuit(oper1, oper2, byte_and=byte_and):
    return (byte_and[(byte_1, byte_2)] for byte_1, byte_2 in input_sequence(oper1, oper2))


def or_circuit(oper1, oper2, byte_or=byte_or):
    return (byte_or[(byte_1, byte_2)] for byte_1, byte_2 in input_sequence(oper1, oper2))


def xor_circuit(oper1, oper2, byte_xor=byte_xor):
    return (byte_xor[(byte_1, byte_2)] for byte_1, byte_2 in input_sequence(oper1, oper2))


def inverter(oper1, byte_inverter=byte_inverter):
    return (byte_inverter[byte, ] for byte in oper1)


def shift_left(oper1, oper2):
    bins = bits(oper1)
    mag = int(oper2) & (len(bins) - 1)
    return pad_right(bins[mag:], z, len(bins))


def shift_right(oper1, oper2):
    bins = bits(oper1)
    mag = int(oper2) & (len(bins) - 1)
    return pad_left(bins[:-mag or len(bins)], msb(bins), len(bins))


def pairwise(iterable):  # "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)