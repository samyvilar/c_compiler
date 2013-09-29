__author__ = 'samyvilar'

from front_end.loader.locations import loc
from itertools import chain
from front_end.parser.types import c_type, IntegralType, VAListType, FloatType
from front_end.parser.types import DoubleType, unsigned
from front_end.parser.ast.expressions import exp

from back_end.virtual_machine.instructions.architecture import ConvertToFloat, ConvertToFloatFromUnsigned
from back_end.virtual_machine.instructions.architecture import ConvertToInteger


def cast_expression(expr, symbol_table, expression_func):
    return cast(
        expression_func(exp(expr), symbol_table, expression_func), c_type(exp(expr)), c_type(expr), loc(expr)
    )


def cast(instrs, from_type, to_type, location):
    # TODO: deal with types of multiple size.
    if isinstance(to_type, VAListType) \
            or from_type == to_type \
            or (isinstance(from_type, IntegralType) and isinstance(to_type, IntegralType)) \
            or (isinstance(from_type, FloatType) and isinstance(to_type, FloatType)):
        return instrs

    if isinstance(to_type, FloatType) and unsigned(from_type):
        return chain(instrs, (ConvertToFloatFromUnsigned(location),))

    if isinstance(from_type, FloatType) and isinstance(to_type, IntegralType):
        return chain(instrs, (ConvertToInteger(location),))

    if isinstance(from_type, IntegralType) and isinstance(to_type, DoubleType):
        return chain(instrs, (ConvertToFloat(location),))

    raise ValueError('{l} Unable to cast from {f} to {t}'.format(l=location, f=from_type, t=to_type))