__author__ = 'samyvilar'

from types import NoneType

from collections import defaultdict
from itertools import izip, chain, ifilter, imap

from math import log

from front_end.loader.locations import LocationNotSet, loc

ids = defaultdict()


def operns(obj):
    return getattr(obj, 'operands', ())


class Instruction(object):  # No operand instruction.
    def __init__(self, location=LocationNotSet, instr_id=None):
        self.instruction_id = instr_id or ids[self.__class__]
        self.location = location

    def name(self):
        return self.__class__.__name__

    def __len__(self):
        return 1

    def __repr__(self):  # Simple instruction has no operands.
        return self.name()

    def __int__(self):
        return self.instruction_id

    def __iter__(self):
        yield self

    def __eq__(self, other):
        return type(other) is type(self)

    def __ne__(self, other):
        return not self.__eq__(other)


class Operand(object):
    def __init__(self, value, location=LocationNotSet):
        self.value = value
        self.location = location

    def __iter__(self):
        yield self


class Integer(Operand):
    def __int__(self):
        return int(self.value)

    def __long__(self):
        return long(self.value)

    def __str__(self):
        return 'Integer ' + str(self.value)

    def __float__(self):
        return float(self.value)


Byte = Integer


class Reference(Integer):
    def __init__(self, obj, location=LocationNotSet):
        if type(obj) in {int, long}:  # If basic integer do nothing.
            super(Reference, self).__init__(obj, location)
        else:  # otherwise get the id of the object.
            super(Reference, self).__init__(id(obj), location)
        self.obj = obj

    def __str__(self):
        return self.__class__.__name__ + ' ' + str(self.obj)


class Address(Reference):  # Address is a special operand since it can take other instructions or labels as operands
    pass


class Offset(Reference):  # similar to Address but mainly used for relative jumps ...
    pass


class Double(Operand):
    def __float__(self):
        return float(self.value)

    def __long__(self):
        return long(self.value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return 'Double ' + str(self.value)


class WideInstruction(Instruction):  # Instruction with a single operand
    def __init__(self, location, operand):
        self.operands = (operand,)
        super(WideInstruction, self).__init__(location)

    def __iter__(self):
        yield self
        for oper in self.operands:
            yield oper

    def __repr__(self):
        return '{oper_name} {operand}'.format(oper_name=self.name(), operand=self.operands[0])

    def __len__(self):
        return 2

    def __setitem__(self, key, value):
        assert key == 0
        self.operands = (value,)

    def __getitem__(self, item):
        return self.operands[item]

    def __eq__(self, other):
        return super(WideInstruction, self).__eq__(other) and self.operands == other.operands

    def __ne__(self, other):
        return not self.__eq__(other)


class Arithmetic(Instruction):
    pass


class Numeric(Arithmetic):
    pass


class Integral(Numeric):
    pass


class Halt(Instruction):
    pass


class Binary(Integral):
    pass


class Associative(Binary):
    pass


class Add(Associative):
    pass


class Subtract(Binary):
    pass


class Compare(Binary):
    pass


class Multiply(Associative):
    pass


class Divide(Binary):
    pass


class Mod(Binary):
    pass


class BitWise(Integral):
    pass


class ShiftLeft(BitWise, Binary):
    pass


class ShiftRight(BitWise, Binary):
    pass


class Or(BitWise, Associative):
    pass


class Xor(BitWise, Associative):
    pass


class And(BitWise, Associative):
    pass


class Unary(Numeric):
    pass


class Not(BitWise, Unary):
    pass


class NumericBinary(Numeric):
    pass


class AddFloat(NumericBinary):
    pass


class SubtractFloat(NumericBinary):
    pass


class CompareFloat(NumericBinary):
    pass


class MultiplyFloat(NumericBinary):
    pass


class DivideFloat(NumericBinary):
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
    def __len__(self):
        return 1 + len(self.operands)

    def __repr__(self):
        return '{oper_name} {operands}'.format(oper_name=self.name(), operand=self.operands)

    def __iter__(self):
        yield self
        for operand in self.operands:
            yield operand


class JumpTable(RelativeJump, VariableLengthInstruction):
    def __init__(self, location, cases):
        default_addr = cases.pop('default')  # pop default address to properly calculate number of cases ...
        operands = [default_addr, Integer(len(cases), location)]
        _sorted_keys = sorted(cases.iterkeys())
        operands.extend(chain(_sorted_keys, (cases[key] for key in _sorted_keys)))

        super(JumpTable, self).__init__(location, operands)

        self.key_indices = {0: 'default'}
        self.key_indices.update(  # indices of operands ...
            (index, addr) for index, addr in enumerate(_sorted_keys, 2 + len(cases))
        )
        cases['default'] = default_addr  # add back default
        self.cases = cases
        self.operands = operands

    def __repr__(self):
        return super(JumpTable, self).name() + str(self.cases)

    def __setitem__(self, key, value):
        if key < 1 + len(self.cases):
            self.operands[key] = value
        else:
            self.cases[self.key_indices[key]] = value


class LoadRegister(Instruction):
    pass


class LoadPointer(LoadRegister):
    pass


class LoadBaseStackPointer(LoadPointer):
    # Pushes the current address of the base stack pointer, used to reference auto variables.
    pass


class SetBaseStackPointer(Instruction):
    pass


class LoadStackPointer(LoadPointer):
    pass


class SetStackPointer(Instruction):
    pass


class LoadInstructionPointer(LoadPointer):
    pass


class Allocate(WideInstruction):
    pass


class Dup(WideInstruction):
    pass


class Swap(WideInstruction):
    pass


class LoadFlagInstruction(LoadRegister):
    pass


class LoadZeroFlag(LoadFlagInstruction):  # numbers equal (sign or unsigned)
    pass


class LoadNonZeroFlag(LoadFlagInstruction):  # numbers don't equal  (sign or unsigned)
    pass


class LoadCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers less than
    pass


class LoadMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers less than
    pass


class LoadNonZeroNonCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers greater than
    pass


class LoadNonZeroNonMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers greater than
    pass


class LoadZeroCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers less than or equal
                                                     # (invert LoadNonZeroNonCarryBorrowFlag)
    pass


class LoadZeroMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers less than or equal
                                                  # invert LoadNonZeroNonMostSignificantBitFlag
                                                  # LoadZeroMostSignificantBitFlag
    pass


class LoadNonCarryBorrowFlag(LoadFlagInstruction):  # unsigned numbers greater than or equal
                                                    # invert LoadCarryBorrowFlag (LoadNonCarryBorrowFlag)
    pass


class LoadNonMostSignificantBitFlag(LoadFlagInstruction):  # signed numbers greater than or equal
                                                     # invert LoadMostSignificantBitFlag (LoadNonMostSignificantBitFlag)
    pass


class Push(WideInstruction):
    pass


class Pop(Instruction):
    pass


class MoveInstruction(Instruction):
    pass


class WideMoveInstruction(MoveInstruction, WideInstruction):
    pass


class Load(WideMoveInstruction):
    pass


class Set(WideMoveInstruction):
    pass


# Postfix increment and decrement instructions are extremely expensive on stack machines.
# As such lets create special instructions that implements them ...
class PostfixUpdate(WideInstruction):
    pass


class ConvertToFloat(Instruction):
    pass


class ConvertToFloatFromUnsigned(Instruction):
    pass


class ConvertToInteger(Instruction):
    pass


class Pass(Instruction):  # Empty instruction similar to NOP
    pass


class SystemCall(Instruction):
    pass


class Call(WideInstruction):
    pass


class Return(WideInstruction):
    pass


ids.update({
    Halt: 255,

    Push: 2,
    Pop: 254,
    Load: 3,
    Set: 252,

    PostfixUpdate: 4,

    Dup: 5,
    Swap: 6,

    LoadBaseStackPointer: 7,
    SetBaseStackPointer: 249,
    LoadStackPointer: 8,
    SetStackPointer: 248,

    LoadInstructionPointer: 246,

    Allocate: 9,

    Compare: 10,
    CompareFloat: 243,

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
    RelativeJump: 25,

    ConvertToFloat: 23,
    ConvertToFloatFromUnsigned: 24,
    ConvertToInteger: 233,

    LoadZeroFlag: 30,   # ==

    LoadCarryBorrowFlag: 31,  # <, unsigned
    LoadMostSignificantBitFlag: 32,  # < signed
    LoadNonZeroNonCarryBorrowFlag: 33,  # > unsigned
    LoadNonZeroNonMostSignificantBitFlag: 34,  # > signed


    LoadZeroMostSignificantBitFlag: 222,  # signed <=
    LoadZeroCarryBorrowFlag: 223,  # unsigned <=

    LoadNonCarryBorrowFlag: 225,  # unsigned >=
    LoadNonMostSignificantBitFlag: 224,  # signed >=

    LoadNonZeroFlag: 226,   # !=

    Pass: 50,

    Call: 127,
    Return: 129,

    SystemCall: 128,
})


def postfix_update(addr, amount, location):
    return chain(addr, (PostfixUpdate(location, amount),))


def call(address, location):
    yield Call(location, address)


def ret(return_size, location):
    yield Return(location, return_size)


def load_instruction_pointer(location):
    yield LoadInstructionPointer(location)


def load_non_zero_carry_borrow_flag(location):
    yield LoadNonZeroNonCarryBorrowFlag(location)


def load_non_zero_non_most_significant_bit_flag(location):
    yield LoadNonZeroNonMostSignificantBitFlag(location)

instr_objs = dict(izip(ids.itervalues(), ids.iterkeys()))
variable_length_instr_ids = dict(ifilter(lambda item: issubclass(item[0], VariableLengthInstruction), ids.iteritems()))
wide_instr_ids = dict(
    ifilter(
        lambda item: issubclass(item[0], WideInstruction) and not issubclass(item[0], VariableLengthInstruction),
        ids.iteritems()
    )
)
no_operand_instr_ids = dict(ifilter(lambda item: not issubclass(item[0], WideInstruction), ids.iteritems()))


def set_instr(stack_instrs, amount, location, addr_instrs=()):
    if amount == 0 and not addr_instrs:
        return chain(stack_instrs, pop(location))
    return chain(stack_instrs, addr_instrs, (Set(location, amount),))


def load(instrs, amount, location):
    for value in instrs:
        yield value
    yield Load(location, amount)


def pop(location):
    yield Pop(location)


def load_instr(instrs, amount, location, addr_instrs=()):
    if amount == 0 and not addr_instrs:
        return pop(location)
    return load(instrs, amount, location)


def dup(amount, location):
    # expensive instruction requiring at a minimum 4 address translations (instr, operand, stack, stack - operand)
    if amount:
        yield Dup(location, amount)


def swap(amount, location):
    # extremely expensive instruction
    # requiring at a minimum 4 address translations (instr, operand, stack, stack - operand)
    # 3 loads and 3 (temp var) sets ...
    if amount:
        yield Swap(location, amount)


def allocate(amount, location):
    if amount:
        yield Allocate(location, -amount)


def jump_table(location, addresses, allocations, switch_max_value, switch_body_instrs):
    return chain((JumpTable(location, addresses),), chain.from_iterable(allocations), switch_body_instrs)


def is_instr(gen, instr_name):
            # we use the __name__ for functions or check instance if its defined as a class ...
    return (getattr(gen, '__name__', '') == instr_name) or isinstance(gen, globals().get(instr_name, NoneType))


def is_load(gen):
    return is_instr(gen, 'load')


class single_iteration(object):
    def __iter__(self):
        # safe guard against multiple calls to __iter__ instruction are/(should be) emitted only once per instance
        if hasattr(self, 'emitted'):
            raise StopIteration
        self.emitted = True
        # if ok call __iter__ on the next object not necessary a base class ...
        return super(single_iteration, self).__iter__()

    def next(self):
        raise TypeError

    def __next__(self):  # P3K uses __next__
        raise TypeError

    def __name__(self):
        return self.__class__.__name__(self)


class instruction(Instruction):  # represents an instruction iterator ...
    def __init__(self, location):
        self.instr_type = next(ifilter(lambda obj_type: obj_type in ids, self.__class__.mro()))
        super(instruction, self).__init__(location, instr_id=ids[self.instr_type])


class push_constant(single_iteration):
    def __init__(self, value, location):
        assert isinstance(value, (int, long, float, Integer, Double))  # safe guard against bad API call ..
        self.value = value
        self.location = location

    def __iter__(self):
        yield Push(loc(self), self.value)


class push_integral(push_constant):
    core_type = long


class push_real(push_constant):
    core_type = float


def push_address(value, location):
    yield Push(location, value)


def push(value, location):
    if isinstance(value, Address):
        return push_address(value, location)
    if isinstance(value, (int, long, Integer)):
        if isinstance(value, int):
            value = push_integral.core_type(value)  # TODO: fix this ...
        return push_integral(value, location)
    if isinstance(value, (float, Double)):
        return push_real(value, location)
    raise ValueError('{l} Expected Address/Integral/Real got {g}'.format(l=location, g=value))


def is_immediate_push(gen):
    return is_instr(gen, 'push_constant')


def get_immediate_pushed_value(instr):
    return instr.value


class arithmetic_operator(instruction):
    func = staticmethod(reduce)

    def __init__(self, *operands, **kwargs):
        self.operands = operands
        super(arithmetic_operator, self).__init__(kwargs.pop('location', LocationNotSet))

    def __iter__(self):
        if all(imap(is_immediate_push, self.operands)) and hasattr(self, 'operator'):
            opern = self.operands[0]
            assert len(set(imap(type, self.operands))) == 1  # safe-guard against mixing types ...
            return iter(
                push(
                    self.func(  # apply python operator on operands converted to python types ...
                        getattr(opern.core_type, self.operator),  # get python operator
                        # get operands and convert them to python type
                        imap(opern.core_type, imap(get_immediate_pushed_value, self.operands))
                    ),
                    self.location
                )
            )

        return chain(chain.from_iterable(self.operands), (self.instr_type(self.location),))


class binary(arithmetic_operator, Binary):
    def __init__(self, left_operand, right_operand, location):
        super(binary, self).__init__(left_operand, right_operand, location=location)

    @property
    def left_operand(self):
        return self.operands[0]

    @left_operand.setter
    def left_operand(self, value):
        self.operands = (value, self.right_operand)

    @property
    def right_operand(self):
        return self.operands[1]

    @right_operand.setter
    def right_operand(self, value):
        self.operands = (self.left_operand, value)


def operand_location(instr):
    return operns(instr)[0], loc(instr)


class identity(binary):
    def __init__(self, left_operand, right_operand, location, value):
        self.identity_value = value
        super(identity, self).__init__(left_operand, right_operand, location)


class left_identity(identity):
    def __iter__(self):
        if is_immediate_push(self.left_operand) and \
           get_immediate_pushed_value(self.left_operand) == self.identity_value:
                return iter(self.right_operand)

        return super(left_identity, self).__iter__()


class associative(binary):
    def __iter__(self):  # first __iter__ in mro for associative operators ...
        # Collapse associative operations +, *, |, & ... (1 + x) + 1 => (2 + x) ... (2 * x) * 4 => 8 * x ...

        # check left operand ...
        if isinstance(self.left_operand, getattr(self, 'instr_type', type)) and is_immediate_push(self.right_operand):
            l, operand = loc(self.right_operand), get_immediate_pushed_value(self.right_operand)
            if is_immediate_push(self.left_operand.left_operand):
                right_operand = get_immediate_pushed_value(self.left_operand.left_operand)
                self.left_operand.left_operand = \
                    iter(self.__class__(push(operand, loc(self)), push(right_operand, l), l))  # collapse ...
                return iter(self.left_operand)

            if is_immediate_push(self.left_operand.right_operand):
                l, right_operand = loc(self.left_operand.right_operand), \
                    get_immediate_pushed_value(self.left_operand.right_operand)
                self.left_operand.right_operand = iter(self.__class__(push(operand, l), push(right_operand, l), l))
                return iter(self.left_operand)

        # check right operand ...
        if isinstance(self.right_operand, getattr(self, 'instr_type', type)) and is_immediate_push(self.left_operand):
            l, operand = loc(self.left_operand), get_immediate_pushed_value(self.left_operand)
            if is_immediate_push(self.right_operand.left_operand):
                right_operand, l = get_immediate_pushed_value(self.right_operand.left_operand),\
                    loc(self.right_operand.left_operand)
                self.right_operand.left_operand = iter(self.__class__(push(operand, l), push(operand, l), l))
                return iter(self.right_operand)

            if is_immediate_push(self.right_operand.right_operand):
                l, right_operand = loc(self.right_operand.right_operand), \
                    get_immediate_pushed_value(self.right_operand.right_operand)
                self.right_operand.right_operand = iter(self.__class__(push(operand, l), push(operand, l), l))
                return iter(self.right_operand)

        # no collapse continue ...
        return super(associative, self).__iter__()


class right_identity(identity):
    def __iter__(self):  # first __iter__ for non-associative binary operators ...
        if is_immediate_push(self.right_operand) and \
           get_immediate_pushed_value(self.right_operand) == self.identity_value:
                return iter(self.left_operand)

        return super(right_identity, self).__iter__()


class __negative_one_identity__(identity):
    def __init__(self, left_operand, right_operand, location):
        super(__negative_one_identity__, self).__init__(left_operand, right_operand, location, -1)


class __zero_identity__(identity):
    def __init__(self, left_operand, right_operand, location):
        super(__zero_identity__, self).__init__(left_operand, right_operand, location, 0)


class __one_identity__(identity):
    def __init__(self, left_operand, right_operand, location):
        super(__one_identity__, self).__init__(left_operand, right_operand, location, 1)


class left_zero_identity(__zero_identity__, left_identity):
    pass


class right_zero_identity(__zero_identity__, right_identity):
    pass


class left_one_identity(__one_identity__, left_identity):
    pass


class right_one_identity(__one_identity__, right_identity):
    pass


class negative_one_identity(__negative_one_identity__, left_identity, right_identity):
    pass


class zero_identity(left_zero_identity, right_zero_identity):
    pass


class one_identity(left_one_identity, right_one_identity):
    pass


class add(single_iteration, zero_identity, associative, Add):
    operator = '__add__'


class add_float(single_iteration, zero_identity, associative, AddFloat):
    operator = '__add__'


class subtract(single_iteration, right_zero_identity, Subtract):
    operator = '__sub__'


class subtract_float(single_iteration, right_zero_identity, SubtractFloat):
    operator = '__sub__'


class convert_to_left_shift(binary):  # converts constant multiplication to faster left shifts ...
    def __iter__(self):
        assert isinstance(self, Associative)  # safe-guard against non-associative instructions (-, /)
        if is_immediate_push(self.right_operand):
            operand, location = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
            if operand and not ((operand - 1) & operand):  # is operand a non-zero power of 2
                return iter(shift_left(self.left_operand, push(
                    push_integral.core_type(log(operand, 2)), location
                ), location))

        if is_immediate_push(self.left_operand):
            operand, location = get_immediate_pushed_value(self.left_operand), loc(self.left_operand)
            if operand and not((operand - 1) & operand):
                return iter(shift_left(self.right_operand, push(
                    push_integral.core_type(log(operand, 2)), location), location))
            self.left_operand = push(operand, location)

        return super(convert_to_left_shift, self).__iter__()


class multiply(single_iteration, one_identity, associative, convert_to_left_shift, Multiply):
    operator = '__mul__'


class multiply_float(single_iteration, one_identity, associative, MultiplyFloat):
    operator = '__mul__'


class convert_to_right_shift(binary):
    def __iter__(self):
        if is_immediate_push(self.right_operand):
            operand, location = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
            if operand and not ((operand - 1) & operand):
                return iter(shift_right(
                    self.left_operand,
                    push(push_integral.core_type(log(operand, 2)), location),
                    location
                ))

        return super(convert_to_right_shift, self).__iter__()


class divide(single_iteration, right_one_identity, Divide):
    operator = '__div__'


class divide_float(single_iteration, right_one_identity, DivideFloat):
    operator = '__div__'


class mod(single_iteration, binary, Mod):
    operator = '__mod__'


class shift_left(single_iteration, right_zero_identity, ShiftLeft):
    operator = '__lshift__'


class shift_right(single_iteration, right_zero_identity, ShiftRight):
    operator = '__rshift__'


class or_bitwise(single_iteration, zero_identity, associative, Or):
    operator = '__or__'


class xor_bitwise(single_iteration, zero_identity, associative, Xor):
    operator = '__xor__'


class and_bitwise(single_iteration, negative_one_identity, associative, And):
    operator = '__and__'


class unary(arithmetic_operator, Unary):
    func = staticmethod(lambda oper, operands: oper(next(iter(operands))))

    def __init__(self, operand, location):
        super(unary, self).__init__(operand, location=location)


class not_bitwise(single_iteration, unary, Not):
    operator = '__invert__'


class convert_to_float(single_iteration, unary, ConvertToFloat):
    operator = '__float__'


class convert_to_int(single_iteration, unary, ConvertToInteger):
    operator = '__' + push_integral.core_type.__name__ + '__'


def convert_to_float_from_unsigned(instr, location):  # Python does not have unsigned numeric types ...
    return chain(instr, (ConvertToFloatFromUnsigned(location),))


def load_stack_pointer(location):
    yield LoadStackPointer(location)


def set_stack_pointer(instrs, location):
    return chain(instrs, (SetStackPointer(location),))


def load_base_stack_pointer(location):
    yield LoadBaseStackPointer(location)


def set_base_stack_pointer(instrs, location):
    return chain(instrs, (SetBaseStackPointer(location),))


def load_zero_flag(location):
    yield LoadZeroFlag(location)


def load_non_zero_flag(location):
    yield LoadNonZeroFlag(location)


def load_carry_borrow_flag(location):
    yield LoadCarryBorrowFlag(location)


def load_most_significant_bit_flag(location):
    yield LoadMostSignificantBitFlag(location)


def load_zero_most_significant_bit_flag(location):
    yield LoadZeroMostSignificantBitFlag(location)


def load_zero_carry_borrow_flag(location):
    yield LoadZeroCarryBorrowFlag(location)


def load_non_carry_borrow_flag(location):
    yield LoadNonCarryBorrowFlag(location)


def load_non_most_significant_bit_flag(location):
    yield LoadNonMostSignificantBitFlag(location)


def halt(location):
    yield Halt(location)


def pass_instr(location):
    yield Pass(location)


def absolute_jump(instr, location):
    return chain(instr, (AbsoluteJump(location),))


def jump_false(instrs, address, location):
    if is_immediate_push(instrs):
        operand, location = get_immediate_pushed_value(instrs), loc(instrs)
        if operand == 0:  # if operand is a constant 0, just use relative_jump instead.
            return relative_jump(address, location)
        return ()  # otherwise omit instruction all together
    return chain(instrs, (JumpFalse(location, address),))


def jump_true(instrs, address, location):
    if is_immediate_push(instrs):
        operand, location = get_immediate_pushed_value(instrs), loc(instrs)
        if operand == 0:  # if operand is zero omit instruction all together
            return ()
        return relative_jump(address, location)  # otherwise just replace with relative jump
    return chain(instrs, (JumpTrue(location, address),))


def relative_jump(address, location):
    yield RelativeJump(location, address)


from copy import deepcopy


def copy_operand(operand):
    if isinstance(operand, (int, long, float)):
        return operand
    if isinstance(operand, (Address, Offset)):
        return operand.__class__(operand.obj, loc(operand))
    if isinstance(operand, (Integer, Double)):
        return operand.__class__(operand.value, loc(operand))
    raise ValueError('Cannot copy operand: {g}'.format(g=operand))


def copy_instruction(instr):
    if isinstance(instr, JumpTable):
        return JumpTable(loc(instr), deepcopy(instr.cases))
    if isinstance(instr, VariableLengthInstruction):
        return instr.__class__(loc(instr), map(copy_operand, operns(instr)))
    if isinstance(instr, WideInstruction):
        return instr.__class__(loc(instr), copy_operand(operns(instr)[0]))
    if isinstance(instr, Instruction):
        return instr.__class__(loc(instr))
    raise ValueError('Expected an instruction got {g}'.format(g=instr))


def compare(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (Compare(location),), chain.from_iterable(flags))


def compare_floats(l_instr, r_instr, location, flags=()):
    return chain(l_instr, r_instr, (CompareFloat(location),), chain.from_iterable(flags))


def value(obj):
    return getattr(obj, 'value', obj)


class logical(binary):
    def __init__(self, left_operand, right_operand, location, operand_types):
        self.operand_types = operand_types
        self.default_instr, self.end_instr = Pass(location), Pass(location)
        super(logical, self).__init__(left_operand, right_operand, location=location)


class logical_and(single_iteration, logical, And):  # it needs to reference an instruction in order to create the object
    def __iter__(self):
        if is_immediate_push(self.left_operand) and is_immediate_push(self.right_operand):
            return iter(  # collapse constants
                push(
                    push_integral.core_type(
                        all(imap(push_real.core_type, imap(get_immediate_pushed_value, self.operands)))
                    ),
                    self.location
                )
            )

        if is_immediate_push(self.left_operand):  # check left operand
            operand, location = get_immediate_pushed_value(self.left_operand), loc(self.left_operand)
            # if left operand is zero than simply push zero otherwise check right operand ...
            # use float just to be safe ...
            return iter(
                compare(self.right_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
                if push_real.core_type(operand)
                else push(0, loc(self))
            )

        if is_immediate_push(self.right_operand):  # check right operand
            # care must be taken if the right operand is constant zero since we still need to evaluate the left,
            # but we really don't need to apply expensive 'compare', simply pop the result ...
            operand, location = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
            return iter(
                compare(self.left_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
                if push_real.core_type(operand)
                else chain(self.left_operand, pop(self.location), push(0, self.location))
            )

        if isinstance(self.left_operand, logical_and):
            # check we are chaining && if so update the left operands false_instr instruction, so it can skip this one
            # or any other && expression.
            # we are parsing using right recursion, so the last operand will iterate first but emit last.
            self.left_operand.right_default_instr = getattr(self, 'right_default_instr', self.default_instr)

        return chain(
            jump_false(
                self.left_operand,
                Offset(getattr(self, 'right_default_instr', self.default_instr), self.location),
                self.location
            ),
            compare(self.right_operand, push(0, self.location), self.location, (load_non_zero_flag(self.location),)),
            relative_jump(Offset(self.end_instr, self.location), self.location),
            (self.default_instr,),
            push(0, self.location),
            (self.end_instr,),
        )


class logical_or(single_iteration, logical, Or):
    def apply(self):
        return push(
            push_integral.core_type(
                bool(value(operns(next(self.left_operand))[0]) or value(operns(next(self.right_operand))[0]))
            ),
            self.location
        )

    def __iter__(self):
        if is_immediate_push(self.left_operand) and is_immediate_push(self.right_operand):
            return iter(
                push(
                    push_integral.core_type(
                        any(imap(push_real.core_type, imap(get_immediate_pushed_value, self.operands)))
                    ),
                    self.location
                )
            )

        if is_immediate_push(self.left_operand):
            operand, location = get_immediate_pushed_value(self.left_operand), loc(self.left_operand)
            return iter(
                compare(self.right_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
                if push_real.core_type(operand)
                else push(1, location)
            )

        if is_immediate_push(self.right_operand):
            # again care must be taken if the right operand is 0, we still need to evaluate the left
            # but no need for COMPARE
            operand, location = get_immediate_pushed_value(self.right_operand), loc(self.right_operand)
            return iter(
                compare(self.left_operand, push(0, location), self.location, (load_non_zero_flag(self.location),))
                if push_real.core_type(operand)
                else chain(self.left_operand, pop(self.location), push(1, location))
            )

        if isinstance(self.left_operand, logical_or):
            self.left_operand.right_default_instr = getattr(self, 'right_default_instr', self.default_instr)

        return chain(
            jump_true(
                self.left_operand,
                Offset(getattr(self, 'right_default_instr', self.default_instr), self.location),
                self.location
            ),
            compare(self.right_operand, push(0, self.location), self.location, (load_non_zero_flag(self.location),)),
            relative_jump(Offset(self.end_instr, self.location), self.location),
            (self.default_instr,),
            push(1, self.location),
            (self.end_instr,),
        )