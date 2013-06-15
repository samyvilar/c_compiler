__author__ = 'samyvilar'

from collections import defaultdict

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import AbsoluteJump
from back_end.virtual_machine.instructions.architecture import JumpTable, JumpFalse, JumpTrue

from back_end.virtual_machine.instructions.stack import __pop
from back_end.virtual_machine.operands import oprn, oprns


def _abs_jump(addr, cpu, mem):
    cpu.instr_pointer = addr


def _rel_jump(addr, cpu, mem):
    _abs_jump(cpu.instr_pointer + addr, cpu, mem)


def _jump_false(value, cpu, mem):
    _jump_true(not value, cpu, mem)


def _jump_true(value, cpu, mem):
    _rel_jump((value and oprn(cpu, mem)) or cpu.word_type(2), cpu, mem)


def _jump_table(value, cpu, mem):
    # get all the operands, the first gives the number of operands in total.
    values = oprns(cpu, mem, oprn(cpu, mem))
    default_addr = values[1]
    table = defaultdict(lambda: default_addr)  # set the default addr
    table.update({values[index]: values[index + 1] for index in xrange(2, len(values), 2)})
    _rel_jump(table[value], cpu, mem)


def jump_instrs(instr, cpu, mem):
    jump_instrs.rules[instr](__pop(instr, cpu, mem), cpu, mem)
jump_instrs.rules = {
    ids[AbsoluteJump]: _abs_jump,
    ids[JumpFalse]: _jump_false,
    ids[JumpTrue]: _jump_true,
    ids[JumpTable]: _jump_table,
}