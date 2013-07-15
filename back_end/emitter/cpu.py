__author__ = 'samyvilar'

from back_end.emitter.object_file import Symbol

from back_end.virtual_machine.instructions.architecture import Instruction, Allocate, Push, Pop, Halt, Pass, operns, Dup
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat
from back_end.virtual_machine.instructions.architecture import And, Or, Xor, Not, ShiftLeft, ShiftRight
from back_end.virtual_machine.instructions.architecture import ConvertToInteger, ConvertToFloat
from back_end.virtual_machine.instructions.architecture import LoadZeroFlag, LoadOverflowFlag, LoadCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import Jump, AbsoluteJump, CompoundSet
from back_end.virtual_machine.instructions.architecture import RelativeJump, JumpTrue, JumpFalse, JumpTable
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer, Load, Set
from back_end.virtual_machine.instructions.architecture import PushFrame, PopFrame, Enqueue, Dequeue, Address, Byte


def pop(cpu, mem):
    cpu.stack_pointer += 1
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
    return oper1 << (oper2 & 0b111111)


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


def _jump(addr, cpu):
    cpu.instr_pointer = addr


def abs_jump(instr, cpu, mem):
    _jump(pop(cpu, mem), cpu)


def rel_jump(instr, cpu, mem):
    _jump(cpu.instr_pointer + operns(instr)[0], cpu)


def jump_if_true(instr, cpu, mem):
    value = pop(cpu, mem)
    if value:
        _jump(cpu.instr_pointer + operns(instr)[0], cpu)
    else:
        _pass(instr, cpu, mem)


def jump_if_false(instr, cpu, mem):
    value = pop(cpu, mem)
    if not value:
        _jump(cpu.instr_pointer + operns(instr)[0], cpu)
    else:
        _pass(instr, cpu, mem)


def jump_table(instr, cpu, mem):
    value = pop(cpu, mem)
    _jump(instr.cases[value].obj.address, cpu)


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


def _dup(instr, cpu, mem):
    value = pop(cpu, mem)
    push(value, cpu, mem)
    push(value, cpu, mem)


def load_base_pointer(instr, cpu, mem):
    push(cpu.base_pointer, cpu, mem)


def load_stack_pointer(instr, cpu, mem):
    push(cpu.stack_pointer, cpu, mem)


def _load(instr, cpu, mem):
    addr, quantity = pop(cpu, mem), operns(instr)[0]
    for addr in xrange(addr, addr + quantity):
        push(mem[addr], cpu, mem)


def _set(instr, cpu, mem):
    addr, quantity = _pop(instr, cpu, mem), operns(instr)[0]
    for addr, value in enumerate(reversed([pop(cpu, mem) for _ in xrange(quantity)]), addr):
        push(value, cpu, mem)
        mem[addr] = value


def _compound_set(instr, cpu, mem):
    for addr, value in enumerate(reversed([pop(cpu, mem) for _ in xrange(operns(instr)[0])]), _pop(instr, cpu, mem)):
        push(value, cpu, mem)
        mem[addr] = value


def _push(instr, cpu, mem):
    push(operns(instr)[0], cpu, mem)


def _pop(instr, cpu, mem):
    return pop(cpu, mem)


def push_frame(instr, cpu, mem):
    cpu.frames.append((cpu.base_pointer, cpu.stack_pointer))
    cpu.base_pointer = cpu.stack_pointer


def pop_frame(instr, cpu, mem):
    cpu.base_pointer, cpu.stack_pointer = cpu.frames.pop()


def enqueue(instr, cpu, mem):
    value = _pop(instr, cpu, mem)
    cpu.queue.append(value)
    push(value, cpu, mem)


def dequeue(instr, cpu, mem):
    push(cpu.queue.pop(0), cpu, mem)


def evaluate(cpu, mem):
    while True:
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
    Dup: _dup,
    Allocate: allocate,
    LoadZeroFlag: lambda instr, cpu, mem: push(cpu.zero, cpu, mem),
    LoadCarryBorrowFlag: lambda instr, cpu, mem: push(cpu.carry, cpu, mem),
    LoadOverflowFlag: lambda instr, cpu, mem: push(cpu.overflow, cpu, mem),

    LoadBaseStackPointer: load_base_pointer,
    LoadStackPointer: load_stack_pointer,

    PushFrame: push_frame,
    PopFrame: pop_frame,

    Enqueue: enqueue,
    Dequeue: dequeue,

    Load: _load,
    Set: _set,
    CompoundSet: _compound_set,
}
evaluate.rules.update({rule: expr for rule in expr.rules})
evaluate.rules.update({rule: jump for rule in jump.rules})


class CPU(object):
    def __init__(self):
        self.frames, self.stack, self.queue = [], [], []
        self.instr_pointer = 0
        self.zero, self.carry, self.overflow = 0, 0, 0
        self._stack_pointer, self.base_pointer = -1, -1

    @property
    def stack_pointer(self):
        return self._stack_pointer

    @stack_pointer.setter
    def stack_pointer(self, value):
        self._stack_pointer = value
        if self._stack_pointer > 0:
            assert False
        if self.stack_pointer > self.base_pointer:
            assert False


def address(curr=0, step=1):
    while True:
        yield curr
        curr += step


def load(instrs, mem, symbol_table, address_gen=None):
    address_gen = iter(address_gen or address())

    for instr in instrs:
        instr.address = next(address_gen)
        mem[instr.address] = instr

    data = {}  # referenced declarations.
    for current_addr, elem in mem.iteritems():
        operands = []
        for operand in operns(elem):
            if isinstance(operand, Address):
                if isinstance(operand.obj, Instruction):
                    ref_addr = operand.obj.address
                elif isinstance(operand.obj, Symbol):
                    symbol = symbol_table[operand.obj.name]
                    if hasattr(symbol, 'address'):
                        ref_addr = symbol.address
                    else:  # it must be a declaration.
                        binaries = (Byte(0, '') for _ in xrange(symbol.size))
                        ref_addr = symbol.address = next(address_gen)
                        data[ref_addr] = next(binaries)
                        data.update({next(address_gen): b for b in binaries})
                        symbol.binaries = True
                else:
                    ref_addr = operand
                if isinstance(elem, RelativeJump):
                    operand = ref_addr - current_addr
                else:
                    operand = ref_addr
            operands.append(operand)
        elem.operands = operands
    mem.update(data)