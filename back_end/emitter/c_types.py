__author__ = 'samyvilar'

from collections import Iterable
from itertools import chain, izip, imap, repeat

from front_end.loader.locations import loc

from front_end.parser.ast.declarations import Declaration, Definition, initialization
from front_end.parser.ast.expressions import ConstantExpression, exp, CastExpression, CompoundLiteral, EmptyExpression

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, VoidType
from front_end.parser.types import StructType, PointerType, ArrayType, c_type, StringType, VAListType, void_pointer_type
from front_end.parser.types import UnionType

from back_end.virtual_machine.instructions.architecture import Integer, Double, Pass, Byte

from back_end.emitter.cpu import word_size


def struct_size(ctype):
    return sum(size(c_type(member)) for member in ctype.members.itervalues())


def union_size(ctype):
    return max(imap(size, imap(c_type, ctype.members.itervalues())))


def array_size(ctype):
    return size(c_type(ctype)) * len(ctype)


def numeric_type(ctype):
    return numeric_type.rules[type(ctype)]
numeric_type.rules = {  # Virtual Machine is word based, all non-composite types are 1 word, 64 bits.
    CharType: word_size,
    ShortType: word_size,
    IntegerType: word_size,
    LongType: word_size,
    PointerType: word_size,
    FloatType: word_size,
    DoubleType: word_size,
}


def machine_types(_type):
    return machine_types.rules[type(_type)]
machine_types.rules = {
    Integer: numeric_type.rules[IntegerType],
    Pass: word_size
}


def size(ctype, overrides=()):
    if type(ctype) in overrides:
        return overrides[type(ctype)]
    return size.rules[type(ctype)](ctype)
size.rules = {                                                     # all non-composite types are 1 word, 64 bits.
    StructType: struct_size,
    UnionType: union_size,
    ArrayType: array_size,
    StringType: array_size,
    VAListType: lambda _: 0
}
size.rules.update(chain(
    izip(numeric_type.rules, repeat(numeric_type)),
    izip(machine_types.rules, repeat(machine_types)),
))


 # The C standard dictates that Void pointers are incremented by 1...
size_extended = lambda ctype: size(ctype, overrides={VoidType: 1})

function_operand_type_sizes = lambda ctype: size(ctype, overrides={
    ArrayType: size(void_pointer_type),
    StringType: size(void_pointer_type),
    VoidType: 0
})


def integral_const(const_exp):
    yield Integer(getattr(const_exp, 'exp', 0), loc(const_exp))


def numeric_const(const_exp):
    yield Double(getattr(const_exp, 'exp', 0.0), loc(const_exp))


def array_const(const_exp):
    if isinstance(getattr(const_exp, 'exp', None), Iterable):
        bins = (binaries(value) for value in exp(const_exp))
    elif isinstance(const_exp, EmptyExpression):
        assert isinstance(c_type(const_exp), ArrayType)
        bins = (binaries(c_type(c_type(const_exp))) for _ in xrange(len(c_type(const_exp))))
    else:
        assert isinstance(const_exp, ArrayType)
        bins = (binaries(c_type(const_exp)) for _ in xrange(len(const_exp)))
    return chain.from_iterable(bins)


def struct_const(const_exp):
    if isinstance(getattr(const_exp, 'exp', None), Iterable):
        bins = (binaries(value) for value in exp(const_exp))
    else:
        assert isinstance(const_exp, StructType)
        bins = imap(binaries, imap(c_type, const_exp.members.itervalues()))
    return chain.from_iterable(bins)


def union_const(const_exp):
    if isinstance(getattr(const_exp, 'exp', None), Iterable):
        # initialize union expression add any remaining default values if initializing to a smaller type then largest
        bins = chain(
            (binaries(value) for value in exp(const_exp)),
            (Byte(0) for _ in xrange(size(c_type(const_exp)) - sum(imap(size, imap(c_type, exp(const_exp))))))
        )
    else:
        assert isinstance(const_exp, UnionType)
        # get largest type ...
        bins = binaries(sorted(imap(c_type, const_exp.members.itervalues()), size)[-1])
    return chain.from_iterable(bins)


def dec_binaries(_):
    return ()


def def_binaries(definition):
    return binaries(initialization(definition))


def const_exp_binaries(const_exp):
    if type(const_exp) in const_exp_binaries.rules:
        return const_exp_binaries.rules[type(const_exp)](const_exp)

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
    UnionType: union_const,
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
    if isinstance(struct_type, UnionType):  # unions can only store one value at a time ...
        return 0

    assert member_exp
    offset = 0
    for name in struct_type:
        if member_exp == name:
            return offset
        offset += size(c_type(struct_type.members[name]))
    raise ValueError

from types import MethodType
bind_load_address_func = MethodType