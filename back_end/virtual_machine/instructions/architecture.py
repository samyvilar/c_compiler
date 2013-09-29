__author__ = 'samyvilar'

from collections import defaultdict
from itertools import izip, chain, ifilter

from front_end.loader.locations import LocationNotSet, loc

ids = defaultdict()


def operns(obj):
    return getattr(obj, 'operands', ())


class Int(long):
    def __new__(cls, number, location=LocationNotSet):
        value = super(Int, cls).__new__(cls, number)
        value.location = location
        value.number = number  # Needed in order to print or else infinite recursion on str()
        return value


class Float(float):
    # noinspection PyInitNewSignature
    def __new__(cls, number, location=LocationNotSet):
        value = super(Float, cls).__new__(cls, number)
        value.location = location
        value.number = number
        return value


class Instruction(tuple):  # No operand instruction.
    def __new__(cls, location=LocationNotSet):
        value = super(Instruction, cls).__new__(cls, (Int(ids[cls], location),))
        value.location = location
        return value

    def name(self):
        return self.__class__.__name__

    def __len__(self):
        return 1

    def __repr__(self):  # Simple instruction has no operands.
        return self.name()

    def __int__(self):
        return self[0]


class Halt(Instruction):
    pass


class Operand(object):
    def __iter__(self):
        yield self


class Integer(Int, Operand):
    pass


Byte = Integer


class Address(Int):  # Address is a special operand since it can take other instructions or labels as operands
    def __new__(cls, obj=0, location=LocationNotSet):
        if type(obj) in {Integer, Int, int, long}:  # If basic integer do nothing.
            value = super(Address, cls).__new__(cls, obj, location)
        else:  # otherwise get the id of the object.
            value = super(Address, cls).__new__(cls, id(obj), location)
        value.obj = obj
        return value

    def __str__(self):
        return 'Address ' + super(Address, self).__str__()


class Double(Float, Operand):
    pass


class WideInstruction(Instruction):  # Instruction with a single operand
    # noinspection PyInitNewSignature
    def __new__(cls, location, operand):
        value = super(WideInstruction, cls).__new__(cls, location)
        if type(operand) in {int, long}:
            value.operands = (Integer(operand, location),)
        else:
            value.operands = (operand,)
        return value

    def __iter__(self):
        yield self[0]
        for oper in self.operands:
            yield oper

    def __repr__(self):
        return '{oper_name} {operand}'.format(oper_name=self.name(), operand=self.operands[0])

    def __len__(self):
        return 2

    def __setitem__(self, key, value):
        assert key == 0
        self.operands = (value,)


class Arithmetic(Instruction):
    pass


class Numeric(Arithmetic):
    pass


class Integral(Numeric):
    pass


class Add(Integral):
    pass


class Subtract(Integral):
    pass


class Multiply(Integral):
    pass


class Divide(Integral):
    pass


class Mod(Integral):
    pass


class BitWise(Integral):
    pass


class ShiftLeft(BitWise):
    pass


class ShiftRight(BitWise):
    pass


class Or(BitWise):
    pass


class Xor(BitWise):
    pass


class And(BitWise):
    pass


class Not(BitWise):
    pass


class AddFloat(Numeric):
    pass


class SubtractFloat(Numeric):
    pass


class MultiplyFloat(Numeric):
    pass


class DivideFloat(Numeric):
    pass


class Jump(Instruction):
    pass


class AbsoluteJump(Jump):
    pass


class RelativeJump(WideInstruction, Jump):
    pass


class JumpFalse(RelativeJump):
    pass


class JumpTrue(RelativeJump):
    pass


class VariableLengthInstruction(WideInstruction):  # Instructions with more than one operand, mainly used for JumpTable
    def __new__(cls, location, operands):
        value = super(VariableLengthInstruction, cls).__new__(cls, location, operands)
        value.operands = operands
        return value

    def __len__(self):
        return 1 + len(self.operands)

    def __repr__(self):
        return '{oper_name} {operands}'.format(oper_name=self.name(), operand=self.operands)

    def __iter__(self):
        yield self[0]
        for operand in self.operands:
            yield operand

    def __setitem__(self, key, value):
        self.operands[key] = value


class JumpTable(RelativeJump, VariableLengthInstruction):
    def __new__(cls, location, cases):
        default_addr = cases.pop('default')  # pop default address to properly calculate number of cases ...
        operands = [Integer(len(cases), location), default_addr]
        operands.extend(chain.from_iterable(cases.iteritems()))
        value = super(JumpTable, cls).__new__(cls, location, operands)
        value.key_indices = {1: 'default'}
        value.key_indices.update(
            (2 * index + 1, addr) for index, addr in enumerate(chain.from_iterable(cases.iterkeys()), 1)
        )
        cases['default'] = default_addr  # add back default
        value.cases = cases
        return value

    def __repr__(self):
        return super(JumpTable, self).name() + str(self.cases)

    def __setitem__(self, key, value):
        super(JumpTable, self).__setitem__(key, value)
        self.cases[self.key_indices[key]] = value


class StackInstruction(Instruction):
    pass


class LoadBaseStackPointer(Instruction):
    # Pushes the current address of the base stack pointer, used to reference auto variables.
    pass


class SetBaseStackPointer(Instruction):
    pass


class LoadStackPointer(Instruction):
    pass


class SetStackPointer(Instruction):
    pass


class LoadFlagInstruction(Instruction):
    pass


class LoadZeroFlag(LoadFlagInstruction):
    pass


class LoadCarryBorrowFlag(LoadFlagInstruction):
    pass


class LoadMostSignificantBit(LoadFlagInstruction):
    pass


class Push(WideInstruction, Integral):
    pass


class Pop(Instruction):
    pass


class MoveInstruction(WideInstruction):
    pass


class Load(MoveInstruction):
    pass


class Set(MoveInstruction):
    pass


class ConvertToFloat(Instruction):
    pass


class ConvertToFloatFromUnsigned(Instruction):
    pass


class ConvertToInteger(Instruction):
    pass


class Mask(Integer):
    pass


class Pass(Instruction):  # Empty instruction similar to NOP
    pass


class SystemCall(Instruction):
    pass


ids.update({
    Halt: 255,

    Push: 2,
    Pop: 254,
    Load: 3,
    Set: 252,

    LoadBaseStackPointer: 7,
    SetBaseStackPointer: 249,
    LoadStackPointer: 8,
    SetStackPointer: 248,

    Add: 11,
    Subtract: 245,

    Multiply: 12,
    Divide: 244,

    Mod: 13,

    ShiftLeft: 14,
    ShiftRight: 242,

    Or: 15,
    And: 241,
    Xor: 16,
    Not: 17,

    AddFloat: 18,
    SubtractFloat: 238,
    MultiplyFloat: 19,
    DivideFloat: 237,

    AbsoluteJump: 20,
    JumpFalse: 21,
    JumpTrue: 235,
    JumpTable: 22,
    RelativeJump: 33,

    ConvertToFloat: 23,
    ConvertToFloatFromUnsigned: 24,
    ConvertToInteger: 233,

    LoadZeroFlag: 30,
    LoadCarryBorrowFlag: 31,
    LoadMostSignificantBit: 32,

    Pass: 50,
    SystemCall: 128,
})

instr_objs = dict(izip(ids.itervalues(), ids.iterkeys()))
variable_length_instr_ids = dict(
    ifilter(lambda item: issubclass(item[0], VariableLengthInstruction), ids.iteritems())
)
wide_instr_ids = dict(
    ifilter(
        lambda item: issubclass(item[0], WideInstruction) and not issubclass(item[0], VariableLengthInstruction),
        ids.iteritems()
    )
)
no_operand_instr_ids = dict(ifilter(lambda item: not issubclass(item[0], WideInstruction), ids.iteritems()))


def dup(amount):
    yield LoadStackPointer(loc(amount))
    yield Push(loc(amount), Address(1, loc(amount)))
    yield Add(loc(amount))
    yield Load(loc(amount), amount)


def swap(amount):
    for i in dup(amount):
        yield i
    yield LoadStackPointer(loc(amount))
    address_offset = Address(1 + 2 * amount, loc(amount))
    yield Push(loc(amount), address_offset)  # skip the two values.
    yield Add(loc(amount))
    yield Load(loc(amount), amount)

    yield LoadStackPointer(loc(amount))  # calculate destination address ...
    yield Push(loc(amount), address_offset)
    yield Add(loc(amount))

    yield Set(loc(amount), Integer(2 * amount, loc(amount)))
    for i in allocate(Integer(-1 * 2 * amount, loc(amount))):
        yield i


def push_frame(location=LocationNotSet):
    yield LoadBaseStackPointer(location)
    yield LoadStackPointer(location)


def pop_frame(argument_len, address_size):
    l = loc(argument_len)
    yield LoadBaseStackPointer(l)  # skip arguments, return address, pointer to return value
    yield Push(l, Address(argument_len + 1 + 2*address_size, l))
    yield Add(l)
    yield Load(l, address_size)
    yield SetStackPointer(l)
    # At this point the stack pointer should just have the previous base pointer on the stack ...
    yield SetBaseStackPointer(l)


def allocate(amount):
    l = loc(amount)
    yield LoadStackPointer(l)
    yield Push(l, Address(-amount, l))
    yield Add(l)
    yield SetStackPointer(l)