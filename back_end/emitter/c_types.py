__author__ = 'samyvilar'

from itertools import chain, izip, imap, repeat, ifilter, takewhile

from utils.rules import set_rules, rules

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, VoidType, EnumType
from front_end.parser.types import StructType, PointerType, ArrayType, c_type, StringType, VAListType, void_pointer_type
from front_end.parser.types import UnionType, unsigned, IntegralType, AddressType
from front_end.parser.types import StrictlySigned, StrictlyUnsigned, FunctionType, members

from front_end.parser.ast.expressions import ConstantExpression

from back_end.virtual_machine.instructions.architecture import Word, Double, Pass, Byte
from back_end.virtual_machine.instructions.architecture import Half, Quarter, OneEighth, DoubleHalf

from back_end.emitter.cpu import float_names, word_names, signed_word_names, word_type_sizes

from back_end.emitter.cpu import word_size, half_word_size, quarter_word_size, one_eighth_word_size
from back_end.emitter.cpu import word_type, half_word_type, quarter_word_type, one_eighth_word_type
from back_end.emitter.cpu import float_size, half_float_size, pack_binaries


def numeric_type_size(ctype):
    return rules(numeric_type_size)[type(ctype)]
set_rules(
    numeric_type_size,
    chain(
        izip((LongType, PointerType, AddressType, DoubleType), repeat(word_size)),
        izip((IntegerType, EnumType, FloatType), repeat(half_word_size)),
        (
            (CharType, one_eighth_word_size),
            (ShortType, quarter_word_size),
        )
    )
)
# numeric_type_size.rules = {
#     CharType: word_size,  # note we have to update vm system calls when working with char_arrays ...
#     ShortType: word_size,
#
#     IntegerType: word_size,
#     EnumType: word_size,
#
#     LongType: word_size,
#     PointerType: word_size,
#
#     FloatType: word_size,
#     DoubleType: word_size,
# }


def struct_size(ctype):
    return sum(imap(size, imap(c_type, members(ctype))))


def union_size(ctype):
    return max(imap(size, imap(c_type, members(ctype))))


def array_size(ctype):
    return size(c_type(ctype)) * len(ctype)


def size(ctype, overrides=None):
    return overrides[type(ctype)] if type(ctype) in (overrides or ()) else rules(size)[type(ctype)](ctype)
size.rules = {
    StructType: struct_size,
    UnionType: union_size,
    ArrayType: array_size,
    StringType: array_size,
    VAListType: lambda _: 0,
    ConstantExpression: lambda e: size(c_type(e))
}
size.rules.update(izip(rules(numeric_type_size), repeat(numeric_type_size)))


 # The C standard dictates that Void pointers are incremented by 1... though you are not allowed to take the sizeof
 # of an expression with an incomplete type such as Void
def size_extended(ctype):
    return size(ctype, overrides={VoidType: 1})


address_types = {ArrayType, StringType, FunctionType, AddressType}


def size_arrays_as_pointers(ctype, overrides=()):
    return size(
        ctype,
        overrides=dict(chain(
            izip(address_types, repeat(size(void_pointer_type))), getattr(overrides, 'iteritems', lambda: overrides)()
        ))
    )


float_sizes_to_words = dict(izip(imap(word_type_sizes.__getitem__, float_names), float_names))  # float word sizes
float_ctypes = set(ifilter(lambda cls: issubclass(cls, FloatType), rules(numeric_type_size).iterkeys()))  # CFloat types
float_ctypes_word_types = dict(izip(    # Convert CType to its size then convert that size to machine word type name
    float_ctypes, imap(float_sizes_to_words.__getitem__, imap(rules(numeric_type_size).__getitem__, float_ctypes))
))

strictly_unsigned_ctypes = set(
    ifilter(lambda cls: issubclass(cls, StrictlyUnsigned), rules(numeric_type_size).iterkeys())
) - float_ctypes  # just to be safe even though floats are strictly signed!
strictly_signed_ctypes = set(
    ifilter(lambda cls: issubclass(cls, StrictlySigned), rules(numeric_type_size).iterkeys())
) - float_ctypes

integral_ctypes = set(ifilter(lambda cls: issubclass(cls, IntegralType), rules(numeric_type_size).iterkeys()))


unsigned_ctypes_to_words = dict(izip(imap(word_type_sizes.__getitem__, word_names), word_names))
unsigned_ctypes = integral_ctypes - (strictly_unsigned_ctypes | strictly_signed_ctypes) | strictly_unsigned_ctypes
unsigned_ctypes_word_types = dict(izip(
    unsigned_ctypes,
    imap(unsigned_ctypes_to_words.__getitem__, imap(rules(numeric_type_size).__getitem__, unsigned_ctypes))
))


signed_ctypes_to_words = dict(izip(imap(word_type_sizes.__getitem__, signed_word_names), signed_word_names))
signed_ctypes = integral_ctypes - (strictly_unsigned_ctypes | strictly_signed_ctypes) | strictly_signed_ctypes
signed_ctypes_word_types = dict(izip(
    signed_ctypes, imap(signed_ctypes_to_words.__getitem__, imap(rules(numeric_type_size).__getitem__, signed_ctypes))
))


def get_word_type_name(ctype):
    return get_word_type_name.rules[unsigned(ctype), type(ctype)]
get_word_type_name.rules = dict(chain(
    # return factory type name based on whether the ctype is unsigned or not and what kind of size it has ...
    izip(izip(repeat(True), unsigned_ctypes_word_types.iterkeys()), unsigned_ctypes_word_types.itervalues()),
    izip(izip(repeat(False), signed_ctypes_word_types.iterkeys()), signed_ctypes_word_types.itervalues()),
    izip(izip(repeat(False), float_ctypes_word_types.iterkeys()), float_ctypes_word_types.itervalues())
))


machine_integral_types = {
    one_eighth_word_size: OneEighth,
    quarter_word_size: Quarter,
    half_word_size: Half,
    word_size: Word,
}
machine_floating_types = {
    half_float_size: DoubleHalf,
    float_size: Double
}


def struct_member_offset(struct_type, member_exp):
    assert member_exp and member_exp in struct_type
    return 0 if isinstance(struct_type, UnionType) else sum(
        imap(size, imap(c_type, imap(struct_type.members.__getitem__, takewhile(member_exp.__ne__, struct_type))))
    )
