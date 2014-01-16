__author__ = 'samyvilar'

import sys
from itertools import izip, repeat, chain, starmap, imap, product
from collections import defaultdict

from struct import pack, unpack

from utils.sequences import exhaust

from logging_config import logging
from back_end.virtual_machine.instructions.architecture import no_operand_instr_ids, wide_instr_ids
from back_end.virtual_machine.instructions.architecture import Push, Pop, Halt, Pass, Jump
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat
from back_end.virtual_machine.instructions.architecture import And, Or, Xor, Not, ShiftLeft, ShiftRight
from back_end.virtual_machine.instructions.architecture import ConvertTo, ConvertToFloatFrom
from back_end.virtual_machine.instructions.architecture import LoadZeroFlag, LoadMostSignificantBitFlag
from back_end.virtual_machine.instructions.architecture import AbsoluteJump, LoadInstructionPointer, LoadCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import RelativeJump, JumpTrue, JumpFalse, JumpTable
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer, Load, Set
from back_end.virtual_machine.instructions.architecture import SetBaseStackPointer, SetStackPointer, SystemCall
from back_end.virtual_machine.instructions.architecture import Allocate, Dup, Swap, LoadNonZeroFlag
from back_end.virtual_machine.instructions.architecture import Integer, Double, PostfixUpdate, Compare, CompareFloat
from back_end.virtual_machine.instructions.architecture import LoadNonCarryBorrowFlag, LoadNonMostSignificantBitFlag
from back_end.virtual_machine.instructions.architecture import LoadNonZeroNonCarryBorrowFlag, LoadZeroCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import LoadNonZeroNonMostSignificantBitFlag
from back_end.virtual_machine.instructions.architecture import LoadZeroMostSignificantBitFlag, Binary, NumericBinary
from back_end.virtual_machine.instructions.architecture import push_integral, push_real, Address

logger = logging.getLogger('virtual_machine')

word_size = 8
machine_integral_type = push_integral.core_type
machine_real_type = push_real.core_type
machine_types = (machine_integral_type, machine_real_type)

interpret_real_as_integral = lambda value: machine_integral_type(unpack('Q', pack('d', float(value)))[0])
interpret_integral_as_real = lambda value: machine_real_type(unpack('d', pack('Q', float(value)))[0])


def pop(cpu, mem):
    cpu.stack_pointer += word_size
    return mem[cpu.stack_pointer]


def peek(cpu, mem, index=word_size):
    return mem[cpu.stack_pointer + index]


def update(value, cpu, mem):
    mem[cpu.stack_pointer + word_size] = value


def push(value, cpu, mem):
    # safeguard against trying to push a non-numeric type (such as an instruction ...)
    if not isinstance(value, (machine_integral_type, machine_real_type, Integer, Double, int)):
        print value, type(value)
        exit(-1)

    mem[cpu.stack_pointer] = value
    cpu.stack_pointer -= word_size


def set_flags(instr, cpu, mem, operand_0, operand_1):
    result = operand_0 - operand_1

    cpu.zero_flag = machine_integral_type(result == 0)
    cpu.non_zero_flag = machine_integral_type(result != 0)

    cpu.most_significant_bit_flag = cpu.carry_borrow_flag = machine_integral_type(result < 0)
    cpu.non_most_significant_bit_flag = cpu.non_carry_borrow_flag = machine_integral_type(result >= 0)
    cpu.zero_most_significant_bit_flag = cpu.zero_carry_borrow_flag = machine_integral_type(result <= 0)
    cpu.non_zero_non_most_significant_bit_flag = cpu.non_zero_non_carry_borrow_flag = machine_integral_type(result > 0)


def compare(instr, cpu, mem, _):
    operand_1 = pop(cpu, mem)
    operand_0 = pop(cpu, mem)
    compare.rules[type(operand_0), type(operand_1), type(instr)](instr, cpu, mem, operand_0, operand_1)
compare.rules = {
    (machine_integral_type, machine_integral_type, Compare): set_flags,

    (machine_integral_type, machine_real_type, Compare): lambda instr, cpu, mem, oper0, oper1:
    set_flags(instr, cpu, mem, oper0, interpret_real_as_integral(oper1)),

    (machine_real_type, machine_integral_type, Compare): lambda instr, cpu, mem, oper0, oper1:
    set_flags(instr, cpu, mem, interpret_real_as_integral(oper0), oper1),

    (machine_real_type, machine_real_type, Compare): lambda instr, cpu, mem, oper0, oper1:
    set_flags(instr, cpu, mem, interpret_real_as_integral(oper0), interpret_real_as_integral(oper1)),


    (machine_real_type, machine_real_type, CompareFloat): set_flags,

    (machine_real_type, machine_integral_type, CompareFloat): lambda instr, cpu, mem, oper0, oper1:
    set_flags(instr, cpu, mem, oper0, interpret_integral_as_real(oper1)),

    (machine_integral_type, machine_real_type, CompareFloat): lambda instr, cpu, mem, oper0, oper1:
    set_flags(instr, cpu, mem, interpret_integral_as_real(oper0), oper1),

    (machine_integral_type, machine_integral_type, CompareFloat): lambda instr, cpu, mem, oper0, oper1:
    set_flags(instr, cpu, mem, interpret_integral_as_real(oper0), interpret_real_as_integral(oper1))
}

compare_float = compare


binary_instr_names = {
    Add: '__add__',
    AddFloat: '__add__',
    Subtract: '__sub__',
    SubtractFloat: '__sub__',
    Multiply: '__mul__',
    MultiplyFloat: '__mul__',
    Divide: '__div__',
    DivideFloat: '__div__',

    And: '__and__',
    Or: '__or__',
    Xor: '__xor__',
    Mod: '__mod__',
    ShiftLeft: '__lshift__',
    ShiftRight: '__rshift__'
}


def _entry(operand_types, instr_type, instructions=binary_instr_names):
    oper1_type, oper2_type = operand_types

    interpret_left_operand = lambda oper, intrp: lambda oper1, oper2, oper=oper, intrp=intrp: oper(intrp(oper1), oper2)
    interpret_right_operand = lambda oper, intrp: lambda oper1, oper2, oper=oper, intrp=intrp: oper(oper1, intrp(oper2))
    interpret_both_operands = lambda oper, intrp: \
        lambda oper1, oper2, oper=oper, intrp=intrp: oper(intrp(oper1), intrp(oper2))

    expected_instr_type = {machine_integral_type: Binary, machine_real_type: NumericBinary}

     # both types ok and match instruction type, do nothing ...
    if oper1_type is oper2_type and issubclass(instr_type, expected_instr_type[oper1_type]):
        _impl = getattr(oper1_type, instructions[instr_type])

    elif issubclass(instr_type, Binary):  # expects both operands to be of integral types ...
        func = getattr(machine_integral_type, instructions[instr_type])
        if oper1_type is machine_real_type and oper2_type is machine_integral_type:
            _impl = interpret_left_operand(func, interpret_real_as_integral)
        elif oper1_type is machine_integral_type and oper2_type is machine_real_type:
            _impl = interpret_right_operand(func, interpret_real_as_integral)
        else:
            _impl = interpret_both_operands(func, interpret_real_as_integral)

    elif issubclass(instr_type, NumericBinary):  # expects both operands to be of real types ...
        func = getattr(machine_real_type, instructions[instr_type])
        if oper1_type is machine_integral_type and oper2_type is machine_real_type:
            _impl = interpret_left_operand(func, interpret_integral_as_real)
        elif oper1_type is machine_real_type and oper2_type is machine_integral_type:
            _impl = interpret_right_operand(func, interpret_integral_as_real)
        else:
            _impl = interpret_both_operands(func, interpret_integral_as_real)

    else:
        raise ValueError('Expected a class of Binary or Numeric subclass got {g}'.format(g=instr_type))

    return (oper1_type, oper2_type, instr_type), _impl


default_binary_implementations = dict(
    starmap(_entry, product(product(machine_types, machine_types), binary_instr_names.iterkeys()))
)


def bin_arithmetic(instr, cpu, mem, implementations=None):
    oper2, oper1 = pop(cpu, mem), pop(cpu, mem)
    return (implementations or default_binary_implementations)[type(oper1), type(oper2), type(instr)](oper1, oper2)
bin_arithmetic.rules = dict(izip(binary_instr_names.iterkeys(), repeat(bin_arithmetic)))


default_unary_implementations = {
    (machine_integral_type, Not): machine_integral_type.__invert__,
    (machine_real_type, Not): lambda operand: machine_integral_type.__invert__(interpret_real_as_integral(operand)),

    (machine_integral_type, ConvertToFloatFrom): machine_real_type,
    (machine_real_type, ConvertToFloatFrom): lambda operand: operand,

    (machine_real_type, ConvertTo): machine_integral_type,
    (machine_integral_type, ConvertTo): lambda operand: operand,
}


def unary_arithmetic(instr, cpu, mem, implementations=None):
    operand = pop(cpu, mem)
    return (implementations or default_unary_implementations)[type(operand), type(instr)](operand)
unary_arithmetic.rules = {Not, ConvertToFloatFrom, ConvertTo}


def expr(instr, cpu, mem, _):
    push(expr.rules[type(instr)](instr, cpu, mem), cpu, mem)
expr.rules = dict(
    chain(
        izip(bin_arithmetic.rules, repeat(bin_arithmetic)),
        izip(unary_arithmetic.rules, repeat(unary_arithmetic))
    )
)


def _jump(addr, cpu, *_):
    cpu.instr_pointer = addr


def abs_jump(instr, cpu, mem):
    _jump(pop(cpu, mem), cpu, mem)


def rel_jump(instr, cpu, mem):
    _jump(cpu.instr_pointer + mem[cpu.instr_pointer + word_size] + instr_size(instr), cpu, mem)


def jump_if_true(instr, cpu, mem):
    _jump(
        cpu.instr_pointer + (mem[cpu.instr_pointer + word_size] * bool(pop(cpu, mem))) + instr_size(instr),
        cpu,
        mem
    )


def jump_if_false(instr, cpu, mem):
    _jump(
        cpu.instr_pointer + (mem[cpu.instr_pointer + word_size] * (not pop(cpu, mem))) + instr_size(instr),
        cpu,
        mem
    )


def jump_table(instr, cpu, mem):
    _jump(
        cpu.instr_pointer
        + machine_integral_type(instr.cases.get(pop(cpu, mem), machine_integral_type(instr.cases['default'].obj)))
        + instr_size(instr),
        cpu,
        mem
    )


def jump(instr, cpu, mem, _):
    jump.rules[type(instr)](instr, cpu, mem)
jump.rules = {
    RelativeJump: rel_jump,
    AbsoluteJump: abs_jump,
    JumpTrue: jump_if_true,
    JumpFalse: jump_if_false,
    JumpTable: jump_table,
}


def instr_size(instr):
    return instr_size.rules[type(instr)]
instr_size.rules = {instr: word_size for instr in no_operand_instr_ids}  # default all instructions to one word
instr_size.rules.update((instr, 2*word_size) for instr in wide_instr_ids)  # wide instructions are 2 words
instr_size.rules[JumpTable] = 2*word_size


def instr_pointer_update(instr):
    return instr_pointer_update.rules[type(instr)]
instr_pointer_update.rules = {JumpTable: 0}  # JumpTable is a variable length instruction ...
for instr in instr_size.rules:  # Make sure not to update the instruction pointer on Jump instructions ...
    instr_pointer_update.rules[instr] = 0 if issubclass(instr, Jump) else instr_size.rules[instr]


def postfix_update(instr, cpu, mem, _):
    addr = peek(cpu, mem)  # get/copy address
    update(mem[addr], cpu, mem)  # replace pushed address with value ...
    mem[addr] += mem[cpu.instr_pointer + word_size]  # update value at address ...


def evaluate(cpu, mem, os=None):
    os = os or Kernel()
    instr = None

    # Convert Operands/Values to native machine/python types ...
    def machine_word(value):
        if isinstance(value, (int, Integer, Address)):
            return machine_integral_type(value)
        if isinstance(value, (float, Double)):
            return machine_real_type(value)
        return value

    mem.update(izip(mem.iterkeys(), imap(machine_word, mem.itervalues())))

    while not isinstance(instr, Halt):
        instr = mem[cpu.instr_pointer]
        _ = evaluate.rules[type(instr)](instr, cpu, mem, os)
        cpu.instr_pointer += instr_pointer_update(instr)
evaluate.rules = {
    Halt: lambda instr, cpu, mem, _: None,  # evaluate will halt ...
    Pass: lambda instr, cpu, mem, _: None,

    Push: lambda instr, cpu, mem, _: push(mem[cpu.instr_pointer + word_size], cpu, mem),
    Pop: lambda instr, cpu, mem, _: pop(cpu, mem),

    LoadNonZeroFlag: lambda instr, cpu, mem, _: push(cpu.non_zero_flag, cpu, mem),
    LoadZeroFlag: lambda instr, cpu, mem, _: push(cpu.zero_flag, cpu, mem),

    LoadCarryBorrowFlag: lambda instr, cpu, mem, _: push(cpu.carry_borrow_flag, cpu, mem),
    LoadMostSignificantBitFlag: lambda instr, cpu, mem, _: push(cpu.most_significant_bit_flag, cpu, mem),

    LoadNonCarryBorrowFlag: lambda instr, cpu, mem, _: push(cpu.non_carry_borrow_flag, cpu, mem),
    LoadNonMostSignificantBitFlag: lambda instr, cpu, mem, _: push(cpu.non_most_significant_bit_flag, cpu, mem),

    LoadNonZeroNonCarryBorrowFlag: lambda instr, cpu, mem, _: push(cpu.non_zero_non_carry_borrow_flag, cpu, mem),
    LoadNonZeroNonMostSignificantBitFlag: lambda instr, cpu, mem, _: push(
        cpu.non_zero_non_most_significant_bit_flag, cpu, mem
    ),

    LoadZeroCarryBorrowFlag: lambda instr, cpu, mem, _: push(cpu.zero_carry_borrow_flag, cpu, mem),
    LoadZeroMostSignificantBitFlag: lambda instr, cpu, mem, _: push(cpu.zero_most_significant_bit_flag, cpu, mem),


    LoadBaseStackPointer: lambda instr, cpu, mem, _: push(cpu.base_pointer, cpu, mem),
    SetBaseStackPointer: lambda instr, cpu, mem, _: setattr(cpu, 'base_pointer', pop(cpu, mem)),
    LoadStackPointer: lambda instr, cpu, mem, _: push(cpu.stack_pointer, cpu, mem),
    SetStackPointer: lambda instr, cpu, mem, _: setattr(cpu, 'stack_pointer', pop(cpu, mem)),
    LoadInstructionPointer: lambda instr, cpu, mem, _: push(cpu.instr_pointer + instr_size(instr), cpu, mem),

    PostfixUpdate: postfix_update,

    Allocate: lambda instr, cpu, mem, _: setattr(
        cpu, 'stack_pointer', cpu.stack_pointer + mem[cpu.instr_pointer + word_size]
    ),

    Dup: lambda instr, cpu, mem, _: exhaust(
        starmap(
            push,
            izip(
                chain.from_iterable(repeat(
                    (pop(cpu, mem) for _ in xrange(mem[cpu.instr_pointer + word_size]/word_size)),
                    2
                )),
                repeat(cpu),
                repeat(mem),
            )
        )
    ),

    Swap: lambda instr, cpu, mem, _: exhaust(
        starmap(
            push,
            izip(
                reversed(pop(cpu, mem) for _ in xrange(mem[cpu.instr_pointer + word_size]/word_size)),
                repeat(cpu),
                repeat(mem),
            )
        )
    ),

    Load: lambda instr, cpu, mem, _: exhaust(
        starmap(
            push,
            izip(
                imap(
                    mem.__getitem__,
                    reversed(xrange(peek(cpu, mem), pop(cpu, mem) + mem[cpu.instr_pointer + word_size], word_size))
                ),
                repeat(cpu),
                repeat(mem)
            )
        )
    ),

    Set: lambda instr, cpu, mem, _: mem.update(
        izip(
            xrange(peek(cpu, mem), pop(cpu, mem) + mem[cpu.instr_pointer + word_size], word_size),
            starmap(
                peek,
                izip(
                    repeat(cpu),
                    repeat(mem),
                    xrange(word_size, mem[cpu.instr_pointer + word_size] + word_size, word_size)
                )
            )
        )
    ),

    Compare: compare,
    CompareFloat: compare_float,

    SystemCall: lambda instr, cpu, mem, os: os.calls[machine_integral_type(pop(cpu, mem))](cpu, mem, os),
}
evaluate.rules.update(chain(izip(expr.rules, repeat(expr)), izip(jump.rules, repeat(jump))))

stdin_file_no = getattr(sys.stdin, 'fileno', lambda: 0)()
stdout_file_no = getattr(sys.stdout, 'fileno', lambda: 1)()
stderr_file_no = getattr(sys.stderr, 'fileno', lambda: 2)()
std_files = ((stdin_file_no, sys.stdin), (stdout_file_no, sys.stdout), (stderr_file_no, sys.stderr))


try:
    from back_end.virtual_machine.c.cpu import c_evaluate as evaluate, CPU, Kernel, VirtualMemory, base_element
except ImportError as er:
    class Kernel(object):
        def __init__(self, calls=None, open_files=std_files):
            self.calls = calls or {}
            self.opened_files = dict(open_files)

    class CPU(object):
        def __init__(self):
            self.instr_pointer = machine_integral_type(0)
            self.stack_pointer, self.base_pointer = machine_integral_type(-word_size), machine_integral_type(-word_size)

            self.flag_names = (
                'zero_flag', 'non_zero_flag',
                'carry_borrow_flag', 'non_carry_borrow_flag',
                'most_significant_bit_flag', 'non_most_significant_bit_flag',
                'non_zero_non_carry_borrow_flag', 'zero_carry_borrow_flag',
                'non_zero_non_most_significant_bit_flag', 'zero_most_significant_bit_flag'
            )

            for flag_name in self.flag_names:
                setattr(self, flag_name, machine_integral_type(0))

    class VirtualMemory(defaultdict):
        def __init__(self, default_factory=machine_integral_type):
            super(VirtualMemory, self).__init__(default_factory)

    evaluate = evaluate

    def base_element(cpu, mem, _):
        return mem[cpu.base_pointer - 1]

    logger.warning('Failed to import C implementations, reverting to Python')