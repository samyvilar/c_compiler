__author__ = 'samyvilar'

import sys

from itertools import izip, count, repeat, chain

from logging_config import logging
from back_end.emitter.object_file import Reference

from back_end.virtual_machine.instructions.architecture import Instruction, Push, Pop, Halt, Pass, operns
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat
from back_end.virtual_machine.instructions.architecture import And, Or, Xor, Not, ShiftLeft, ShiftRight
from back_end.virtual_machine.instructions.architecture import ConvertToInteger, ConvertToFloat
from back_end.virtual_machine.instructions.architecture import LoadZeroFlag, LoadOverflowFlag, LoadCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import Jump, AbsoluteJump
from back_end.virtual_machine.instructions.architecture import RelativeJump, JumpTrue, JumpFalse, JumpTable
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer, Load, Set
from back_end.virtual_machine.instructions.architecture import Address, Byte
from back_end.virtual_machine.instructions.architecture import SetBaseStackPointer, SetStackPointer


logger = logging.getLogger('virtual_machine')


def pop(cpu, mem):
    cpu.stack_pointer += 1
    return mem[cpu.stack_pointer]


def push(value, cpu, mem):
    assert isinstance(value, (int, float, long))
    mem[cpu.stack_pointer] = value
    cpu.stack_pointer -= 1


def add(oper1, oper2):
    return oper1 + oper2


def sub(oper1, oper2):
    return oper1 - oper2


def mult(oper1, oper2):
    return oper1 * oper2


def div(oper1, oper2):
    return oper1 / oper2


def _and(oper1, oper2):
    return oper1 & oper2


def _or(oper1, oper2):
    return oper1 | oper2


def _xor(oper1, oper2):
    return oper1 ^ oper2


def mod(oper1, oper2):
    return oper1 % oper2


def _shift_left(oper1, oper2):
    return oper1 << (oper2 & 0b111111)


def _shift_right(oper1, oper2):
    return oper1 >> oper2


def _not(oper1):
    return ~oper1


def convert_to_int(oper1):
    return long(oper1)


def convert_to_float(oper1):
    return float(oper1)


def bin_arithmetic(instr, cpu, mem):
    oper2, oper1 = pop(cpu, mem), pop(cpu, mem)
     # make sure emitter doesn't generate instr that mixes types.
    if not (isinstance(oper1, (int, long)) and isinstance(oper2, (int, long)) or
            isinstance(oper1, float) and isinstance(oper2, float)):
        raise ValueError('Bad operands!')
    result = bin_arithmetic.rules[type(instr)](oper1, oper2)
    if isinstance(instr, (Add, AddFloat, Subtract, SubtractFloat, Multiply, MultiplyFloat, Divide, DivideFloat)):
        cpu.overflow = cpu.carry = bool(result < 0)
        cpu.zero = bool(not result)
    return result
bin_arithmetic.rules = {
    Add: add,
    AddFloat: add,
    Subtract: sub,
    SubtractFloat: sub,
    Multiply: mult,
    MultiplyFloat: mult,
    Divide: div,
    DivideFloat: div,
    And: _and,
    Or: _or,
    Xor: _xor,
    Mod: mod,
    ShiftLeft: _shift_left,
    ShiftRight: _shift_right,
}


def unary_arithmetic(instr, cpu, mem):
    return unary_arithmetic.rules[type(instr)](pop(cpu, mem))
unary_arithmetic.rules = {
    Not: _not,
    ConvertToFloat: convert_to_float,
    ConvertToInteger: convert_to_int,
}


def expr(instr, cpu, mem):
    push(expr.rules[type(instr)](instr, cpu, mem), cpu, mem)
expr.rules = {rule: bin_arithmetic for rule in bin_arithmetic.rules}
expr.rules.update(izip(unary_arithmetic.rules, repeat(unary_arithmetic)))


def _jump(addr, cpu, mem):
    cpu.instr_pointer = addr


def abs_jump(instr, cpu, mem):
    _jump(pop(cpu, mem), cpu, mem)


def rel_jump(instr, cpu, mem):
    _jump(cpu.instr_pointer + operns(instr)[0], cpu, mem)


def jump_if_true(instr, cpu, mem):
    value = pop(cpu, mem)
    if value:
        _jump(cpu.instr_pointer + operns(instr)[0], cpu, mem)
    else:
        _pass(instr, cpu, mem)


def jump_if_false(instr, cpu, mem):
    value = pop(cpu, mem)
    if not value:
        _jump(cpu.instr_pointer + operns(instr)[0], cpu, mem)
    else:
        _pass(instr, cpu, mem)


def jump_table(instr, cpu, mem):
    _jump(instr.cases.get(pop(cpu, mem), instr.cases['default']).obj.address, cpu, mem)


def jump(instr, cpu, mem):
    jump.rules[type(instr)](instr, cpu, mem)
jump.rules = {
    RelativeJump: rel_jump,
    AbsoluteJump: abs_jump,
    JumpTrue: jump_if_true,
    JumpFalse: jump_if_false,
    JumpTable: jump_table,
}


def allocate(instr, cpu, mem):
    cpu.stack_pointer -= operns(instr)[0]


def _pass(instr, cpu, mem):
    cpu.instr_pointer += 1


# def _dup(instr, cpu, mem):
#     load_stack_pointer(instr, cpu, mem)
#     push(Address(1, loc(instr)), cpu, mem)
#     expr(Add(), cpu, mem)
#     _load(Load(loc(instr), operns(instr)[0]), cpu, mem)
#
#
# def _swap(instr, cpu, mem):
#     _dup(Dup(loc(instr), operns(instr)[0]), cpu, mem)  # duplicate initial value ...
#
#     load_stack_pointer(instr, cpu, mem)  # load second value ...
#     address_offset = Address(1 + 2 * operns(instr)[0], loc(instr))
#     _push(Push(loc(instr), address_offset), cpu, mem)  # skip the two values.
#     expr(Add(), cpu, mem)
#     _load(Load(loc(instr), operns(instr)[0]), cpu, mem)
#
#     load_stack_pointer(instr, cpu, mem)  # calculate destination address ...
#     _push(Push(loc(instr), address_offset), cpu, mem)
#     expr(Add(), cpu, mem)
#
#     _set(Set(loc(instr), Integer(2 * operns(instr)[0], loc(instr))), cpu, mem)  # copy swap values to orig location
#     allocate(Allocate(loc(instr), Integer(-1 * 2 * operns(instr)[0], loc(instr))), cpu, mem)  # deallocate copies ...


def load_base_pointer(instr, cpu, mem):
    push(cpu.base_pointer, cpu, mem)


def set_base_pointer(instr, cpu, mem):
    cpu.base_pointer = _pop(instr, cpu, mem)


def load_stack_pointer(instr, cpu, mem):
    push(cpu.stack_pointer, cpu, mem)


def set_stack_pointer(instr, cpu, mem):
    cpu.stack_pointer = pop(cpu, mem)


def _load(instr, cpu, mem):
    addr, quantity = pop(cpu, mem), operns(instr)[0]
    for addr in reversed(xrange(addr, addr + quantity)):
        push(mem[addr], cpu, mem)


def stepper(initial_value=0, step=1):
    while True:
        yield initial_value
        initial_value += step


def _set(instr, cpu, mem):
    addr, quantity, stack_pointer = _pop(instr, cpu, mem), operns(instr)[0], cpu.stack_pointer + 1
    for addr, stack_addr in izip(xrange(addr, addr + quantity), xrange(stack_pointer, stack_pointer + quantity)):
        mem[addr] = mem[stack_addr]


def _push(instr, cpu, mem):
    push(operns(instr)[0], cpu, mem)


def _pop(instr, cpu, mem):
    return pop(cpu, mem)


def evaluate(cpu, mem, os=None):
    os = os or Kernel()
    while True:
        if cpu.instr_pointer in os.calls:
            os.calls[cpu.instr_pointer](cpu, mem, os)

        instr = mem[cpu.instr_pointer]
        if isinstance(instr, Halt):
            break
        evaluate.rules[type(instr)](instr, cpu, mem)
        if not isinstance(instr, (Pass, Jump)):  # do not update instr pointer, this instrs manipulate it.
            _pass(instr, cpu, mem)
evaluate.rules = {
    Pass: _pass,
    Push: _push,
    Pop: _pop,

    LoadZeroFlag: lambda instr, cpu, mem: push(cpu.zero, cpu, mem),
    LoadCarryBorrowFlag: lambda instr, cpu, mem: push(cpu.carry, cpu, mem),
    LoadOverflowFlag: lambda instr, cpu, mem: push(cpu.overflow, cpu, mem),

    LoadBaseStackPointer: load_base_pointer,
    SetBaseStackPointer: set_base_pointer,
    LoadStackPointer: load_stack_pointer,
    SetStackPointer: set_stack_pointer,

    Load: _load,
    Set: _set,
}
evaluate.rules.update(chain(izip(expr.rules, repeat(expr)), izip(jump.rules, repeat(jump))))
# evaluate.rules.update((rule, expr) for rule in expr.rules)
# evaluate.rules.update((rule, jump) for rule in jump.rules)

stdin_file_no = getattr(sys.stdin, 'fileno', lambda: 0)()
stdout_file_no = getattr(sys.stdout, 'fileno', lambda: 1)()
stderr_file_no = getattr(sys.stderr, 'fileno', lambda: 2)()
std_files = {stdin_file_no: sys.stdin, stdout_file_no: sys.stdout, stderr_file_no: sys.stderr}


class Kernel(object):
    def __init__(self, calls=None):
        self.opened_files = {stdin_file_no: sys.stdin, stdout_file_no: sys.stdout, stderr_file_no: sys.stderr}
        self.calls = calls or {}


class CPU(object):
    def __init__(self):
        self.frames = []
        self.instr_pointer = 1024
        self.zero, self.carry, self.overflow = 0, 0, 0
        self._stack_pointer, self.base_pointer = -1, -1

    @property
    def stack_pointer(self):
        return self._stack_pointer

    @stack_pointer.setter
    def stack_pointer(self, value):
        self._stack_pointer = value
        if self._stack_pointer > 0:
            raise ValueError('stack pointer cannot be positive got {g}'.format(g=self._stack_pointer))
        # if self.stack_pointer > self.base_pointer:
        #     raise ValueError('Stack corruption base_pointer {b} exceeding stack_pointer {s}'.format(
        #         b=self.base_pointer, s=self.stack_pointer
        #     ))


address = lambda curr=1024, step=1: count(curr, step)


def load(instrs, mem, symbol_table=None, address_gen=None):
    address_gen = iter(address_gen or address())
    symbol_table = symbol_table or {}

    references = {}
    for instr in instrs:
        instr.address = next(address_gen)
        mem[instr.address] = instr
        if any(isinstance(o, Address) for o in operns(instr)):
            references[instr.address] = instr

    for addr, instr in references.iteritems():
        operands = []
        for o in operns(instr):
            obj = getattr(o, 'obj', None)
            if hasattr(obj, 'address'):
                ref_addr = o.obj.address
            elif isinstance(obj, Reference):
                symbol = symbol_table[o.obj.name]
                if hasattr(symbol, 'first_element'):
                    ref_addr = symbol.first_element.address
                else:
                    ref_addr = next(address_gen)
                    symbol.first_element = Byte(0, '')
                    symbol.first_element.address = ref_addr
                    mem[symbol.first_element.address] = symbol.first_element
                    mem.update({next(address_gen): Byte(0, '') for _ in xrange(symbol.size - 1)})
            else:
                assert not isinstance(obj, Instruction)  # Make sure we are not referencing omitted instruction
                ref_addr = o
            operands.append(ref_addr - (addr if isinstance(instr, RelativeJump) else 0))
        instr.operands = operands