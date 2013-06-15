__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import LoadCarryBorrowFlag, LoadOverflowFlag, LoadZeroFlag

from back_end.virtual_machine.instructions.stack import _push


def _load_carry_flag(instr, cpu, mem):
    _push(cpu.carry, cpu, mem)


def _load_overflow_flag(instr, cpu, mem):
    _push(cpu.overflow, cpu, mem)


def _load_zero_flag(instr, cpu, mem):
    _push(cpu.zero, cpu, mem)


def load_flag_instrs(instr, cpu, mem):
    load_flag_instrs.rules[instr](instr, cpu, mem)
load_flag_instrs.rules = {
    ids[LoadCarryBorrowFlag]: _load_carry_flag,
    ids[LoadOverflowFlag]: _load_overflow_flag,
    ids[LoadZeroFlag]: _load_zero_flag,
}
