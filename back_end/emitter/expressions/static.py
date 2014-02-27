__author__ = 'samyvilar'

from itertools import imap, chain, repeat, izip

from utils.sequences import consume, peek_or_terminal, terminal, consume_all
from utils.rules import set_rules, rules

from front_end.loader.locations import loc, LocationNotSet

from front_end.parser.ast.expressions import exp, ConstantExpression, CastExpression, EmptyExpression, SizeOfExpression
from front_end.parser.ast.expressions import CompoundLiteral, Initializer, get_expressions, BinaryExpression

from front_end.parser.declarations.declarations import Declaration, Definition, initialization

from front_end.parser.types import c_type, members, CType
from front_end.parser.types import StructType, ArrayType, PointerType, UnionType, StringType, integral_types, real_types

from back_end.emitter.c_types import size, machine_integral_types, machine_floating_types, pack_binaries
from back_end.virtual_machine.instructions.architecture import Byte, Address, Pass


def static_integral_ctype(ctype, value=0, location=LocationNotSet):
    yield machine_integral_types[size(ctype)](value, location or loc(ctype))


def static_integral_exp(expr):
    return static_integral_ctype(c_type(expr), exp(expr), loc(expr))


def static_real_ctype(ctype, value=0.0, location=LocationNotSet):
    yield machine_floating_types[size(ctype)](value, location or loc(ctype))


def static_real_exp(expr):
    return static_real_ctype(c_type(expr), exp(expr), loc(expr))


def static_array_ctype(ctype):
    return chain.from_iterable(imap(binaries, repeat(c_type(ctype), len(ctype))))


def static_array_exp(expr):
    return chain.from_iterable(imap(binaries, exp(expr)))


def static_struct_ctype(ctype):
    return chain.from_iterable(imap(binaries, imap(c_type, members(ctype))))


def static_struct_exp(expr):
    return chain.from_iterable(imap(binaries, exp(expr)))


def static_union_ctype(ctype):
    return static_binaries(max(imap(c_type, members(ctype)), key=size))


def static_union_exp(expr):
    return chain(
        imap(binaries, exp(expr)[0]), imap(Byte, repeat(0, size(c_type(expr)) - size(c_type(exp(expr)[0]))))
    )


def static_dec_binaries(_):
    return ()


def static_def_binaries(definition, default_bins=()):
    instrs = static_binaries(initialization(definition), default_bins)
    # TODO: deal with static pointer initialized by address types ...
    assert isinstance(initialization(definition), (EmptyExpression, Initializer, ConstantExpression))
    return instrs


def static_ctype_binaries(ctype):
    return rules(static_ctype_binaries)[type(ctype)](ctype)
set_rules(
    static_ctype_binaries,
    chain(
        izip(integral_types, repeat(static_integral_ctype)),
        izip(real_types, repeat(static_real_ctype)),
        (
            (ArrayType, static_array_ctype),
            (StructType, static_struct_ctype),
            (UnionType, static_union_ctype),
            (StringType, static_array_ctype)
        )
    )
)


def static_exp_binaries(const_exp):
    return rules(static_exp_binaries)[type(c_type(const_exp))](const_exp)
set_rules(
    static_exp_binaries,
    chain(
        izip(integral_types, repeat(static_integral_exp)), izip(real_types, repeat(static_real_exp)),
        (
            (ArrayType, static_array_exp), (StringType, static_array_exp),
            (StructType, static_struct_exp), (UnionType, static_union_exp),
        )
    )
)


def static_cast_expr(obj):
    if isinstance(exp(obj), (ConstantExpression, CastExpression)):
        return static_binaries(exp(obj))
    raise ValueError('{l} Could not generate binaries for {g}'.format(l=loc(obj), g=obj))


def static_compound_literal(expr):
    return chain.from_iterable(imap(binaries, exp(expr).itervalues()))


def static_initializer(expr):
    return chain.from_iterable(imap(binaries, get_expressions(expr)))


def binaries(obj):
    return rules(binaries)[type(obj)](obj)
set_rules(
    binaries,
    chain(
        (
            (Declaration, static_dec_binaries),
            (Definition, static_def_binaries),
            (CastExpression, static_cast_expr),
            (CompoundLiteral, static_compound_literal),
            (Initializer, static_initializer),
            (EmptyExpression, lambda expr: static_ctype_binaries(c_type(expr))),
            (ConstantExpression, static_exp_binaries)
        ),
        izip(rules(static_ctype_binaries), repeat(static_ctype_binaries)),
    )
)


def static_binaries(obj, default_bins=()):
    instrs = binaries(obj)
    return pack_binaries(iter(default_bins) if peek_or_terminal(instrs) is terminal else consume_all(instrs))


from types import MethodType
bind_load_address_func = MethodType
