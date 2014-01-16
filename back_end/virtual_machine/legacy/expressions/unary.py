__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.architecture import ids
from back_end.virtual_machine.instructions.architecture import Not, ConvertTo, ConvertToFloatFrom
from back_end.virtual_machine.legacy.instructions.stack import __pop, _push


def _not(oper1, cpu, mem):
    return ~oper1


def _convert_to_float(oper1, cpu, mem):
    return cpu.word_type(float(oper1))


def _convert_to_int(oper1, cpu, mem):
    return cpu.word_type(int(oper1))


def unary_instrs(instr, cpu, mem):
    _push(unary_instrs.rules[instr](__pop(instr, cpu, mem), cpu, mem), cpu, mem)
unary_instrs.rules = {
    ids[Not]: _not,
    ids[ConvertToFloatFrom]: _convert_to_float,
    ids[ConvertTo]: _convert_to_int,
}