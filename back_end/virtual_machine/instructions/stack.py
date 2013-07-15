__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import Push, Pop, Load, Set, Enqueue, Dequeue, Dup
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer, Allocate
from back_end.virtual_machine.instructions.architecture import PushFrame, PopFrame

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


queue = []


def _enqueue(instr, cpu, mem):
    queue.append(__pop(instr, cpu, mem))


def _dequeue(instr, cpu, mem):
    _push(queue.pop(0), cpu, mem)


def _dup(instr, cpu, mem):
    value = __pop(instr, cpu, mem)
    _push(value, cpu, mem)
    _push(value, cpu, mem)


def _load_base_stack_pointer(instr, cpu, mem):
    _push(cpu.base_stack_pointer, cpu, mem)


def _load_stack_pointer(instr, cpu, mem):
    _push(cpu.stack_pointer, cpu, mem)


def _allocate(instr, cpu, mem):
    cpu.stack_pointer -= oprn(cpu, mem)

frames = []


def _push_frame(instr, cpu, mem):
    frames.append((cpu.base_stack_pointer, cpu.stack_pointer))
    cpu.base_stack_pointer = cpu.stack_pointer


def _pop_frame(instr, cpu, mem):
    cpu.base_stack_pointer, cpu.stack_pointer = frames.pop()


stack_pointers = []


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

    ids[Enqueue]: _enqueue,
    ids[Dequeue]: _dequeue,

    ids[LoadBaseStackPointer]: _load_base_stack_pointer,
    ids[LoadStackPointer]: _load_stack_pointer,
    ids[Allocate]: _allocate,
    ids[Dup]: _dup,

    ids[PushFrame]: _push_frame,
    ids[PopFrame]: _pop_frame,
}
stack_instrs.rules.update({rule: move_instrs for rule in move_instrs.rules})