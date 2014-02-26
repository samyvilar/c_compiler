__author__ = 'samyvilar'

from itertools import chain

from utils.rules import set_rules
from front_end.loader.locations import loc
from front_end.parser.ast.expressions import TernaryExpression, exp, left_exp, right_exp

from back_end.virtual_machine.instructions.architecture import Pass, Offset, relative_jump, get_jump_false

from back_end.emitter.c_types import c_type, size_arrays_as_pointers


def ternary_expression(expr, symbol_table):
    if_false_instr, end_of_conditional_instr = Pass(loc(expr)), Pass(loc(expr))
    expression = symbol_table['__ expression __']
    return chain(
        get_jump_false(size_arrays_as_pointers(c_type(exp(expr))))(
            expression(exp(expr), symbol_table),
            Offset(if_false_instr, loc(expr)),
            loc(expr)
        ),
        expression(left_exp(expr), symbol_table),
        relative_jump(Offset(end_of_conditional_instr, loc(end_of_conditional_instr)), loc(expr)),
        (if_false_instr,),
        expression(right_exp(expr), symbol_table),
        (end_of_conditional_instr,),
    )
set_rules(ternary_expression, {TernaryExpression})
