__author__ = 'samyvilar'

from itertools import izip, chain
from collections import defaultdict
from back_end.emitter.types import flatten
from back_end.emitter.object_file import Symbol

from back_end.virtual_machine.instructions.architecture import Allocate, Push, Pop, Halt, Pass, operns, Instruction, Dup
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat
from back_end.virtual_machine.instructions.architecture import And, Or, Xor, Not, ShiftLeft, ShiftRight
from back_end.virtual_machine.instructions.architecture import ConvertToInteger, ConvertToFloat
from back_end.virtual_machine.instructions.architecture import LoadZeroFlag, LoadOverflowFlag, LoadCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import Jump, AbsoluteJump, Address
from back_end.virtual_machine.instructions.architecture import RelativeJump, JumpTrue, JumpFalse, JumpTable
from back_end.virtual_machine.instructions.architecture import SaveStackPointer, RestoreStackPointer
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer, Load, Set, Swap


def pop(cpu, mem):
    cpu.stack_pointer += 1
    assert cpu.stack_pointer < 0
    return mem[cpu.stack_pointer]


def push(value, cpu, mem):
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
    return oper1 << (oper2 & 0x111111)


def _shift_right(oper1, oper2):
    return oper1 >> oper2


def _not(oper1):
    return ~oper1


def convert_to_int(oper1):
    return int(oper1)


def convert_to_float(oper1):
    return float(oper1)


def bin_arithmetic(instr, cpu, mem):
    oper2, oper1 = pop(cpu, mem), pop(cpu, mem)
     # make sure emitter doesn't generate instr that mixes types.
    assert isinstance(oper1, int) and isinstance(oper2, int) or isinstance(oper1, float) and isinstance(oper2, float)
    result = bin_arithmetic.rules[type(instr)](oper1, oper2)
    if isinstance(instr, (Add, AddFloat, Subtract, SubtractFloat, Multiply, MultiplyFloat, Divide, DivideFloat)):
        cpu.overflow = cpu.carry = int(result < 0)
        cpu.zero = int(not result)
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
expr.rules.update({rule: unary_arithmetic for rule in unary_arithmetic.rules})


def abs_jump(addr, instr, cpu, mem):
    cpu.instr_pointer = addr


def rel_jump(addr, instr, cpu, mem):
    abs_jump(cpu.instr_pointer + addr, instr, cpu, mem)


def jump_if_true(value, instr, cpu, mem):
    if value:
        rel_jump(operns(instr)[0], instr, cpu, mem)
    else:
        _pass(instr, cpu, mem)


def jump_if_false(value, instr, cpu, mem):
    if not value:
        jump_if_true(operns(instr)[0], instr, cpu, mem)
    else:
        _pass(instr, cpu, mem)


def jump_table(value, instr, cpu, mem):
    abs_jump(instr.cases[value].obj.address, instr, cpu, mem)


def jump(instr, cpu, mem):
    jump.rules[type(instr)](pop(cpu, mem), instr, cpu, mem)
jump.rules = {
    AbsoluteJump: abs_jump,
    JumpTrue: jump_if_true,
    JumpFalse: jump_if_false,
    JumpTable: jump_table,
}


def allocate(instr, cpu, mem):
    cpu.stack_pointer -= operns(instr)[0]


def _pass(instr, cpu, mem):
    cpu.instr_pointer += 1


def _dup(instr, cpu, mem):
    value = pop(cpu, mem)
    push(value, cpu, mem)
    push(value, cpu, mem)


def save_stack_pointer(instr, cpu, mem):
    cpu.stack.append(cpu.stack_pointer)


def restore_stack_pointer(instr, cpu, mem):
    cpu.stack_pointer = cpu.stack.pop()


def load_base_pointer(instr, cpu, mem):
    push(cpu.base_pointer, cpu, mem)


def load_stack_pointer(instr, cpu, mem):
    push(cpu.stack_pointer, cpu, mem)


def _load(instr, cpu, mem):
    addr, quantity = pop(cpu, mem), operns(instr)[0]
    for addr in xrange(addr, addr + quantity):
        push(mem[addr], cpu, mem)


def _set(instr, cpu, mem):
    addr, quantity = pop(cpu, mem), operns(instr)[0]
    for addr, value in enumerate(reversed([pop(cpu, mem) for _ in xrange(quantity)]), addr):
        push(value, cpu, mem)
        mem[addr] = value


def swap(instr, cpu, mem):
    value_1, value_2 = pop(cpu, mem), pop(cpu, mem)
    push(value_1, cpu, mem)
    push(value_2, cpu, mem)


def evaluate(cpu, mem):
    while True:
        instr = mem[cpu.instr_pointer]
        if isinstance(instr, Halt):
            break
        evaluate.rules[type(instr)](instr, cpu, mem)
        if not isinstance(instr, (Pass, Jump)):
            _pass(instr, cpu, mem)
evaluate.rules = {
    Pass: _pass,
    Push: lambda instr, cpu, mem: push(operns(instr)[0], cpu, mem),
    Pop: lambda instr, cpu, mem: pop(cpu, mem),
    Dup: _dup,
    Allocate: allocate,
    LoadZeroFlag: lambda instr, cpu, mem: push(cpu.zero, cpu, mem),
    LoadCarryBorrowFlag: lambda instr, cpu, mem: push(cpu.carry, cpu, mem),
    LoadOverflowFlag: lambda instr, cpu, mem: push(cpu.overflow, cpu, mem),

    SaveStackPointer: save_stack_pointer,
    RestoreStackPointer: restore_stack_pointer,
    LoadBaseStackPointer: load_base_pointer,
    LoadStackPointer: load_stack_pointer,

    Load: _load,
    Set: _set,
    Swap: swap,
}
evaluate.rules.update({rule: expr for rule in expr.rules})
evaluate.rules.update({rule: jump for rule in jump.rules})


def address(start, step):
    while True:
        yield start
        start += step


def load(instrs, mem, symbol_table):
    address_space = address(0, 1)
    for addr, instr in izip(address_space, flatten(chain(instrs, (Halt('__EOP__'),)), Instruction)):
        mem[addr] = instr
        instr.address = addr

    for current_addr, instr in mem.iteritems():
        operands = []
        for operand in operns(instr):
            if isinstance(operand, Address):
                if isinstance(operand.obj, Instruction):
                    addr = operand.obj.address
                elif isinstance(operand.obj, Symbol):
                    addr = next(flatten(symbol_table[operand.obj.name].binaries)).address
                else:
                    addr = operand
                if isinstance(instr, RelativeJump):
                    operand = addr - current_addr
                else:
                    operand = addr
            operands.append(operand)
        instr.operands = operands


class CPU(object):
    def __init__(self):
        self.stack, self.queue = [], []
        self.instr_pointer = 0
        self.zero, self.carry, self.overflow = 0, 0, 0
        self.stack_pointer, self.base_pointer = -1, -1