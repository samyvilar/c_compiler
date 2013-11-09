__author__ = 'samyvilar'

from itertools import chain

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import TernaryExpression, exp, left_exp, right_exp

from back_end.virtual_machine.instructions.architecture import jump_false, Pass, Offset, relative_jump


def ternary_expression(expr, symbol_table, expr_func):
    if_false_instr, end_of_conditional_instr = Pass(loc(expr)), Pass(loc(expr))
    return chain(
        jump_false(
            expr_func(exp(expr), symbol_table, expr_func),
            Offset(if_false_instr, loc(expr)),
            loc(expr)
        ),
        expr_func(left_exp(expr), symbol_table, expr_func),
        relative_jump(Offset(end_of_conditional_instr, loc(end_of_conditional_instr)), loc(expr)),
        (if_false_instr,),
        expr_func(right_exp(expr), symbol_table, expr_func),
        (end_of_conditional_instr,),
    )
ternary_expression.rules = {TernaryExpression}
