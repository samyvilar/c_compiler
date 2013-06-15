__author__ = 'samyvilar'

from back_end.virtual_machine.instructions.expressions.arithmetic import arithmetic_instrs
from back_end.virtual_machine.instructions.expressions.bit import bit_instrs

from back_end.virtual_machine.instructions.stack import _push, __pop


def binary_instrs(instr, cpu, mem):
    oper2, oper1 = __pop(instr, cpu, mem), __pop(instr, cpu, mem)
    _push(binary_instrs.rules[instr](instr, oper1, oper2, cpu, mem), cpu, mem)
binary_instrs.rules = {rule: arithmetic_instrs for rule in arithmetic_instrs.rules}
binary_instrs.rules.update({rule: bit_instrs for rule in bit_instrs.rules})
