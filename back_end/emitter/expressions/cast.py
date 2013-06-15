__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.parser.types import c_type, base_c_type, NumericType, IntegralType
from front_end.parser.ast.expressions import exp

from back_end.virtual_machine.instructions.architecture import ConvertToFloat, ConvertToInteger


def cast_expression(expr, symbol_table, stack, expression_func, jump_props):
    return cast_expression.rules[base_c_type(c_type(exp(expr))), base_c_type(c_type(expr))](
        expression_func(exp(expr), symbol_table, stack, expression_func, jump_props), loc(expr),
    )
cast_expression.rules = {
    # Cast FromType,    ToType
    (IntegralType, IntegralType): lambda binaries, location: binaries,
    (NumericType, NumericType): lambda binaries, location: binaries,
    (IntegralType, NumericType): lambda binaries, location: binaries + [ConvertToFloat(location)],
    (NumericType, IntegralType): lambda binaries, location: binaries + [ConvertToInteger(location)],
}


def cast(instrs, from_type, to_type, location):
    if from_type == to_type:
        return instrs
    return cast_expression.rules[base_c_type(from_type), base_c_type(to_type)](instrs, location)