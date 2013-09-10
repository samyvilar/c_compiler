__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import Push, Pop, Load, Set
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer

from back_end.virtual_machine.operands import oprn


def _pop(cpu, mem):
    return __pop(None, cpu, mem)


def _push(value, cpu, mem):
    mem[cpu.stack_pointer] = value
    cpu.stack_pointer -= cpu.word_type(1)


def __pop(instr, cpu, mem):
    cpu.stack_pointer += cpu.word_type(1)
    return mem[cpu.stack_pointer]


def __push(instr, cpu, mem):
    _push(oprn(cpu, mem), cpu, mem)


def _load_base_stack_pointer(instr, cpu, mem):
    _push(cpu.base_stack_pointer, cpu, mem)


def _load_stack_pointer(instr, cpu, mem):
    _push(cpu.stack_pointer, cpu, mem)


def _load(addr, quantity, cpu, mem):
    one = cpu.word_type(1)
    while quantity:
        _push(mem[addr], cpu, mem)
        addr += one
        quantity -= one


def _set(addr, quantity, cpu, mem):  # Set has to set the value backwards, since Load pushes them forward.
    one = cpu.word_type(1)
    stack_pointer = cpu.stack_pointer  # Set does not pop values from the stack only the address
    while quantity:
        quantity -= one
        stack_pointer += one
        mem[addr + quantity] = mem[stack_pointer]


def move_instrs(instr, cpu, mem):
    move_instrs.rules[instr](_pop(cpu, mem), oprn(cpu, mem), cpu, mem)
move_instrs.rules = {
    ids[Load]: _load,
    ids[Set]: _set,
}


def stack_instrs(instr, cpu, mem):
    return stack_instrs.rules[instr](instr, cpu, mem)
stack_instrs.rules = {
    ids[Push]: __push,  # _push is widely used by other instructions...
    ids[Pop]: __pop,

    ids[LoadBaseStackPointer]: _load_base_stack_pointer,
    ids[LoadStackPointer]: _load_stack_pointer,
}
stack_instrs.rules.update({rule: move_instrs for rule in move_instrs.rules})