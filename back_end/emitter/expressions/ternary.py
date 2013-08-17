__author__ = 'samyvilar'

from itertools import chain

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import TernaryExpression, exp, left_exp, right_exp

from back_end.virtual_machine.instructions.architecture import JumpFalse, Pass, Address, RelativeJump


def ternary_expression(expr, symbol_table, expr_func):
    if_false_instr, end_of_cond_instr = Pass(loc(expr)), Pass(loc(expr))
    return chain(
        expr_func(exp(expr), symbol_table, expr_func),
        (JumpFalse(loc(expr), Address(if_false_instr, loc(expr))),),
        expr_func(left_exp(expr), symbol_table, expr_func),
        (RelativeJump(loc(expr), Address(end_of_cond_instr, loc(end_of_cond_instr))),),
        (if_false_instr,),
        expr_func(right_exp(expr), symbol_table, expr_func),
        (end_of_cond_instr,),
    )
ternary_expression.rules = {TernaryExpression}
