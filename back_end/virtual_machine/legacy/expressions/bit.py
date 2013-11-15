__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import ShiftLeft, ShiftRight, Or, And, Xor


def _shift_left(oper1, oper2):
    return oper1 << oper2


def _shift_right(oper1, oper2):
    return oper1 >> oper2


def _or(oper1, oper2):
    return oper1 | oper2


def _and(oper1, oper2):
    return oper1 & oper2


def _xor(oper1, oper2):
    return oper1 ^ oper2


def bit_instrs(instr, oper1, oper2, cpu, mem):
    return bit_instrs.rules[instr](oper1, oper2)
bit_instrs.rules = {
    ids[ShiftLeft]: _shift_left,
    ids[ShiftRight]: _shift_right,

    ids[Or]: _or,
    ids[And]: _and,
    ids[Xor]: _xor,
}
