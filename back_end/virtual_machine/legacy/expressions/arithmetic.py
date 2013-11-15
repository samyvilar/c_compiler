__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat


def _add(oper1, oper2):
    return oper1 + oper2


def _sub(oper1, oper2):
    return oper1 - oper2


def _mul(oper1, oper2):
    return oper1 * oper2


def _div(oper1, oper2):
    return oper1 / oper2


def _mod(oper1, oper2):
    return oper1 % oper2


def _add_float(oper1, oper2):
    return _add(oper1, oper2)


def _sub_float(oper1, oper2):
    return _sub(oper1, oper2)


def _mul_float(oper1, oper2):
    return _mul(oper1, oper2)


def _div_float(oper1, oper2):
    return _div(oper1, oper2)


def arithmetic_instrs(instr, oper1, oper2, cpu, mem):
    result = arithmetic_instrs.rules[instr](oper1, oper2)

    cpu.carry = cpu.word_type(int(getattr(result, 'carry', False)))
    cpu.overflow = cpu.word_type(int(getattr(result, 'overflow', False)))
    cpu.zero = cpu.word_type(int(getattr(result, 'zero', False)))

    return result

arithmetic_instrs.rules = {
    ids[Add]: _add,
    ids[Subtract]: _sub,

    ids[Multiply]: _mul,
    ids[Divide]: _div,

    ids[Mod]: _mod,

    ids[AddFloat]: _add_float,
    ids[SubtractFloat]: _sub_float,
    ids[MultiplyFloat]: _mul_float,
    ids[DivideFloat]: _div_float,
}
