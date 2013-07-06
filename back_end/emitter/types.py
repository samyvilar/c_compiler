__author__ = 'samyvilar'

from collections import defaultdict, Iterable

from front_end.loader.locations import loc

from front_end.parser.ast.declarations import Declaration, Definition, initialization, Extern
from front_end.parser.ast.expressions import ConstantExpression, exp

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType
from front_end.parser.types import StructType, PointerType, ArrayType, c_type, StringType, CType

from back_end.virtual_machine.instructions.architecture import Integer, Double


def error_type(ctype):
    raise ValueError('{l} Trying to get size of incomplete CType'.format(l=loc(ctype)))


def struct_size(ctype):
    return sum(size(c_type(member)) for member in ctype.itervalues())


def array_size(ctype):
    return size(c_type(ctype)) * len(ctype)


def size(ctype):
    return size.rules[type(ctype)](ctype)
size.rules = defaultdict(lambda: lambda ctype: Integer(1, loc(ctype)))  # Virtual Machine is word based
size.rules.update({                                                     # all non-composite types are 1 word, 64 bits.
    type: error_type,
    CType: error_type,
    StructType: struct_size,
    ArrayType: array_size,
    StringType: array_size,
})


def integral_const(const_exp):
    yield Integer(getattr(const_exp, 'exp', 0), loc(const_exp))


def numeric_const(const_exp):
    yield Double(getattr(const_exp, 'exp', 0.0), loc(const_exp))


def array_const(const_exp):
    if isinstance(exp(const_exp), Iterable):
        return (binaries(value) for value in exp(const_exp))
    return (binaries(c_type(const_exp)) for _ in xrange(len(c_type(const_exp))))


def struct_const(const_exp):
    if isinstance(exp(const_exp), Iterable):
        return (binaries(value) for value in exp(const_exp))
    return (binaries(c_type(member)) for member in c_type(const_exp).itervalues())


def dec_binaries(declaration):
    return ()


def def_binaries(definition):
    return binaries(initialization(definition))


def const_exp_binaries(const_exp):
    return const_exp_binaries.rules[type(c_type(const_exp))](const_exp)
const_exp_binaries.rules = {
    CharType: integral_const,
    ShortType: integral_const,
    IntegerType: integral_const,
    LongType: integral_const,
    PointerType: integral_const,
    FloatType: numeric_const,
    DoubleType: numeric_const,

    ArrayType: array_const,
    StringType: array_const,
    StructType: struct_const,
}


def binaries(obj):
    return binaries.rules[type(obj)](obj)
binaries.rules = {
    Declaration: dec_binaries,
    Definition: def_binaries,
    ConstantExpression: const_exp_binaries,
}
binaries.rules.update({rule: const_exp_binaries for rule in const_exp_binaries.rules})


def struct_member_offset(struct_type, member_exp):
    assert member_exp
    offset = 0
    for name in struct_type:
        if member_exp == name:
            return offset
        offset += size(c_type(struct_type[name]))
    raise ValueError
