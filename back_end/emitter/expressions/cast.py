__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc
from itertools import chain, repeat, imap
from front_end.parser.types import c_type, IntegralType, VAListType, FloatType, base_c_type, NumericType
from front_end.parser.types import DoubleType, unsigned, PointerType, ArrayType, void_pointer_type
from front_end.parser.ast.expressions import exp

import back_end.virtual_machine.instructions.architecture as architecture

from back_end.emitter.c_types import size, size_arrays_as_pointers


def cast_expression(expr, symbol_table):
    return cast(symbol_table['__ expression __'](exp(expr), symbol_table), c_type(exp(expr)), c_type(expr), loc(expr))


def cast(instrs, from_type, to_type, location):
    # print from_type, '-->', to_type
    if isinstance(to_type, VAListType) or from_type == to_type:
        # if to_type is undefined or both types are identical do nothing ...
        return instrs

    to_kind, from_kind = imap(base_c_type, (to_type, from_type))
    to_size, from_size = imap(size_arrays_as_pointers, (to_type, from_type))
    if from_kind == to_kind and from_size == to_size:
        # if the conversion, doesn't change the kind/size of the value do nothing ....
        return instrs

    assert not isinstance(to_type, ArrayType)  # cannot cast to an ArrayType
    to_unsigned, from_unsigned = imap(unsigned, (to_type, from_type))

    names = {
        IntegralType: {
            True: architecture.integral_conversion_postfixes,   # unsigned integral type
            False: architecture.signed_conversion_postfixes     # signed
        },
        NumericType: {
            True: architecture.float_conversion_postfixes,
            False: architecture.float_conversion_postfixes
        }
    }

    to_names = names[to_kind][to_unsigned]
    from_names = names[from_kind][from_unsigned]  # if from_unsigned is signed
    if from_kind == NumericType and to_kind == IntegralType:  # converting real to integral, ignore sign ...
        to_names = names[IntegralType][True]

    return getattr(architecture, architecture.get_conversion_name(to_names[to_size], from_names[from_size]))(
        instrs, location
    )
