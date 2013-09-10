__author__ = 'samyvilar'

from collections import Iterable
from itertools import chain, izip, imap, repeat

from front_end.loader.locations import loc

from front_end.parser.ast.declarations import Declaration, Definition, initialization
from front_end.parser.ast.expressions import ConstantExpression, exp, CastExpression, CompoundLiteral, EmptyExpression

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType
from front_end.parser.types import StructType, PointerType, ArrayType, c_type, StringType, VAListType

from back_end.virtual_machine.instructions.architecture import Integer, Double, Pass


def struct_size(ctype):
    return sum(size(c_type(member)) for member in ctype.members.itervalues())


def array_size(ctype):
    return size(c_type(ctype)) * len(ctype)


def numeric_type(ctype):
    return numeric_type.rules[type(ctype)]
numeric_type.rules = {  # Virtual Machine is word based, all non-composite types are 1 word, 64 bits.
    CharType: 1,
    ShortType: 1,
    IntegerType: 1,
    LongType: 1,
    PointerType: 1,
    FloatType: 1,
    DoubleType: 1,
}


def machine_types(_type):
    return machine_types.rules[type(_type)]
machine_types.rules = {
    Integer: numeric_type.rules[IntegerType],
    Pass: 1
}


def size(ctype):
    return size.rules[type(ctype)](ctype)
size.rules = {                                                     # all non-composite types are 1 word, 64 bits.
    StructType: struct_size,
    ArrayType: array_size,
    StringType: array_size,
    VAListType: lambda _: Integer(0, loc(_))
}
size.rules.update(chain(
    izip(numeric_type.rules, repeat(numeric_type)),
    izip(machine_types.rules, repeat(machine_types)),
))


def integral_const(const_exp):
    yield Integer(getattr(const_exp, 'exp', 0), loc(const_exp))


def numeric_const(const_exp):
    yield Double(getattr(const_exp, 'exp', 0.0), loc(const_exp))


def array_const(const_exp):
    if isinstance(exp(const_exp), Iterable):
        bins = (binaries(value) for value in exp(const_exp))
    else:
        bins = (binaries(c_type(const_exp)) for _ in xrange(len(c_type(const_exp))))
    return chain.from_iterable(bins)


def struct_const(const_exp):
    if isinstance(exp(const_exp), Iterable):
        bins = (binaries(value) for value in exp(const_exp))
    else:
        bins = (binaries(c_type(member)) for member in c_type(const_exp).itervalues())
    return chain.from_iterable(bins)


def dec_binaries(_):
    return ()


def def_binaries(definition):
    return binaries(initialization(definition))


def const_exp_binaries(const_exp):
    assert isinstance(const_exp, ConstantExpression)
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


def cast_expr(obj):
    if isinstance(exp(obj), (ConstantExpression, CastExpression)):
        return binaries(exp(obj).__class__(exp(exp(obj)), c_type(obj), loc(obj)))
    else:
        raise ValueError('{l} Could not generate binaries for {g}'.format(l=loc(obj), g=obj))


def compound_literal(expr):
    return chain.from_iterable(imap(binaries, expr))


def binaries(obj):
    return binaries.rules[type(obj)](obj)
binaries.rules = {
    Declaration: dec_binaries,
    Definition: def_binaries,
    EmptyExpression: const_exp_binaries,
    ConstantExpression: const_exp_binaries,
    CastExpression: cast_expr,
    CompoundLiteral: compound_literal,
}
binaries.rules.update(izip(const_exp_binaries.rules, repeat(const_exp_binaries)))


def struct_member_offset(struct_type, member_exp):
    assert member_exp
    offset = 0
    for name in struct_type:
        if member_exp == name:
            return offset
        offset += size(c_type(struct_type.members[name]))
    raise ValueError

from types import MethodType
bind_load_address_func = MethodType