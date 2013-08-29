__author__ = 'samyvilar'

from front_end.loader.locations import loc
from itertools import chain
from front_end.parser.types import c_type, base_c_type, NumericType, IntegralType, PointerType, VAListType
from front_end.parser.ast.expressions import exp

from back_end.virtual_machine.instructions.architecture import ConvertToFloat, ConvertToInteger


def cast_expression(expr, symbol_table, expression_func):
    if c_type(expr) == c_type(c_type(exp(expr))):
        return expression_func(exp(expr), symbol_table, expression_func)
    return cast_expression.rules[base_c_type(c_type(exp(expr))), base_c_type(c_type(expr))](
        expression_func(exp(expr), symbol_table, expression_func), loc(expr)
    )
cast_expression.rules = {
    # Cast FromType,    ToType
    (PointerType, PointerType): lambda binaries, location: binaries,
    (PointerType, IntegralType): lambda binaries, location: binaries,
    (IntegralType, PointerType): lambda binaries, location: binaries,

    (IntegralType, IntegralType): lambda binaries, location: binaries,
    (NumericType, NumericType): lambda binaries, location: binaries,
    (IntegralType, NumericType): lambda binaries, location: chain(binaries, (ConvertToFloat(location),)),
    (NumericType, IntegralType): lambda binaries, location: chain(binaries, (ConvertToInteger(location),)),
}


def cast(instrs, from_type, to_type, location):
    if from_type == to_type:
        return instrs
    elif isinstance(to_type, VAListType):  # TODO: deal with types of multiple size.
        return instrs
    return cast_expression.rules[base_c_type(from_type), base_c_type(to_type)](instrs, location)