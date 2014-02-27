__author__ = 'samyvilar'

import sys
import inspect

from itertools import izip, imap, ifilter, repeat, starmap, takewhile
from utils.sequences import exhaust

from loggers import logging

from front_end.loader.locations import loc, LocationNotSet, Location
from front_end.tokenizer.tokens import TOKENS

from utils import get_attribute_func

logger = logging.getLogger('parser')
current_module = sys.modules[__name__]


class StrictlySigned(object):
    @property
    def unsigned(self):
        return False


class StrictlyUnsigned(object):
    @property
    def unsigned(self):
        return True


class SignType(object):
    pass


class StrictlyIncomplete(object):
    @property
    def rank(self):
        return 0

    @property
    def supported_operations(self):
        return set()

    @property
    def unsigned(self):
        raise TypeError('{l} {ctype} does not support signed/unsigned'.format(l=loc(self), ctype=self))

    @property
    def incomplete(self):
        return True


class CType(StrictlyIncomplete):
    def __init__(self, location=LocationNotSet):
        self.location = location

    @property
    def c_type(self):
        return self

    @c_type.setter
    def c_type(self, _c_type):
        raise TypeError('{l} {c_type} is not a chained type, chaining {to}'.format(
            c_type=self, to=_c_type, l=loc(self)
        ))

    def __call__(self, location):
        return self.__class__(location)

    def __repr__(self):
        return self.__class__.__name__

    def __eq__(self, other):
        return type(self) is type(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self.rank > other.rank

    def __lt__(self, other):
        return self.rank < other.rank

    def __nonzero__(self):
        return 0


class ConcreteType(CType):
    @property
    def incomplete(self):
        return False

    def __nonzero__(self):
        return 1


class CoreType(ConcreteType):  # used to describe core types ...
    pass


class VoidType(CoreType):
    pass

LOGICAL_OPERATIONS = {
    TOKENS.EXCLAMATION,
    TOKENS.GREATER_THAN, TOKENS.LESS_THAN,
    TOKENS.EQUAL_EQUAL, TOKENS.NOT_EQUAL, TOKENS.GREATER_THAN_OR_EQUAL, TOKENS.LESS_THAN_OR_EQUAL,
    TOKENS.LOGICAL_AND, TOKENS.LOGICAL_OR
}

ARITHMETIC_OPERATIONS = {TOKENS.PLUS, TOKENS.MINUS, TOKENS.STAR, TOKENS.FORWARD_SLASH}
COMPOUND_ARITHMETIC_OPERATIONS = {TOKENS.PLUS_EQUAL, TOKENS.MINUS_EQUAL, TOKENS.STAR_EQUAL, TOKENS.FORWARD_SLASH_EQUAL}
BITWISE_OPERATIONS = {
    TOKENS.TILDE, TOKENS.AMPERSAND, TOKENS.BAR, TOKENS.CARET, TOKENS.PERCENTAGE, TOKENS.SHIFT_LEFT, TOKENS.SHIFT_RIGHT,
}
COMPOUND_BITWISE_OPERATIONS = {
    TOKENS.AMPERSAND_EQUAL, TOKENS.BAR_EQUAL, TOKENS.CARET_EQUAL, TOKENS.SHIFT_LEFT_EQUAL, TOKENS.SHIFT_RIGHT_EQUAL,
    TOKENS.PERCENTAGE_EQUAL,
}

COMPOUND_OPERATIONS = {TOKENS.EQUAL} | COMPOUND_ARITHMETIC_OPERATIONS | COMPOUND_BITWISE_OPERATIONS

FUNCTION_CALL_OPERATOR = TOKENS.LEFT_PARENTHESIS + TOKENS.RIGHT_PARENTHESIS
SUBSCRIPT_OPERATOR = TOKENS.LEFT_BRACKET + TOKENS.RIGHT_BRACKET
MEMBER_ACCESS_OPERATOR = TOKENS.DOT
MEMBER_ACCESS_THROUGH_POINTER_OPERATOR = TOKENS.ARROW


def get_supported_operations(ctype):
    return getattr(ctype, 'supported_operations')


class NumericType(ConcreteType):
    supported_operations = LOGICAL_OPERATIONS | ARITHMETIC_OPERATIONS | COMPOUND_OPERATIONS  # TODO check for lvalue


class IntegralType(NumericType):  # Integral types support all the same as Numeric including bitwise operation.
    supported_operations = get_supported_operations(NumericType) | BITWISE_OPERATIONS

    def __init__(self, location=LocationNotSet, unsigned=False):
        self._unsigned = unsigned
        super(IntegralType, self).__init__(location)

    def __gt__(self, other):
        if self.rank == other.rank and unsigned(self) != unsigned(other):  # same rank but diff sign
            return unsigned(self)
        return super(IntegralType, self).__gt__(other)

    def __lt__(self, other):
        if self.rank == other.rank and unsigned(self) != unsigned(other):  # same rank but diff sign
            return not unsigned(self)
        return super(IntegralType, self).__lt__(other)

    def __call__(self, location):
        return self.__class__(location, unsigned=unsigned(self))

    @property
    def unsigned(self):
        return self._unsigned

    @unsigned.setter
    def unsigned(self, value):
        self._unsigned = value


class CharType(IntegralType, CoreType):
    rank = 1


class IntegerType(IntegralType, CoreType):
    rank = 3


class FloatType(StrictlySigned, NumericType, CoreType):
    rank = 7


class DoubleType(FloatType, CoreType):
    rank = 8


class VAListType(CType):
    pass


class ChainedType(CType):
    def __init__(self, ctype, location=LocationNotSet):
        self.__c_type = ctype
        super(ChainedType, self).__init__(location)

    @property
    def c_type(self):
        return self.__c_type

    @c_type.setter
    def c_type(self, _c_type):
        if isinstance(self, FunctionType) and isinstance(_c_type, ArrayType):
            raise ValueError('{l} Functions are not allowed to return {r}'.format(l=loc(_c_type), r=_c_type))
        self.__c_type = _c_type

    def __eq__(self, other):
        return super(ChainedType, self).__eq__(other) and c_type(self) == c_type(other)

    @property
    def incomplete(self):
        return incomplete(c_type(self))


class WidthType(ChainedType, IntegralType):
    def __init__(self, ctype=None, location=LocationNotSet, unsigned=False):
        assert not isinstance(ctype, Location)
        ctype = ctype or IntegerType(location, unsigned=unsigned)
        super(WidthType, self).__init__(ctype, location)
        self.unsigned = unsigned

    def __call__(self, location=LocationNotSet):
        return self.__class__(c_type(self)(location), location, unsigned=self.unsigned)

    @property
    def rank(self):
        return c_type(self).rank

    @property
    def incomplete(self):
        return False


class ShortType(WidthType, CoreType):
    rank = 2


class LongType(WidthType, CoreType):
    rank = 4


class PointerType(ChainedType, IntegralType, StrictlyUnsigned, CoreType):
    rank = 5
    supported_operations = LOGICAL_OPERATIONS | {
        TOKENS.PLUS, TOKENS.MINUS, TOKENS.PLUS_EQUAL, TOKENS.MINUS_EQUAL, SUBSCRIPT_OPERATOR
    }

    def __call__(self, location):
        return self.__class__(c_type(self)(location), location)

    def __repr__(self):
        return 'Pointer to {to}'.format(to=c_type(self))

    def __nonzero__(self):
        return bool(c_type(self))


class AddressType(PointerType):
    pass


class ArrayType(PointerType):
    def __init__(self, __c_type, length, location=LocationNotSet):
        self.length = length
        super(ArrayType, self).__init__(__c_type, location)

    def __call__(self, location):
        return self.__class__(c_type(self)(location), len(self), location)

    def __len__(self):
        return self.length

    def __repr__(self):
        return "Array of {of}".format(of=self.c_type)

    @property
    def const(self):
        return True

    @property
    def incomplete(self):
        return self.length is not None and incomplete(super(ArrayType, self))


class StringType(ArrayType):
    def __init__(self, length, location=LocationNotSet):
        super(StringType, self).__init__(CharType(location), length, location)

    def __call__(self, location):
        return StringType(len(self), location)


class FunctionType(ChainedType, list):
    supported_operations = {FUNCTION_CALL_OPERATOR}

    def __init__(self, ctype, arguments=(), location=LocationNotSet):
        super(FunctionType, self).__init__(ctype, location)
        list.__init__(self, arguments or ())

    def __call__(self, location):
        return self.__class__(c_type(self)(location), list(self), location)

    def __repr__(self):
        return 'FunctionType returning {c_type} accepting ({arguments})'.format(
            c_type=c_type(self), arguments=''.join(repr(arg) + ', ' for arg in self),
        )

    def __eq__(self, other):
        return super(FunctionType, self).__eq__(other) and len(self) == len(other) and all(
            c_type(s) == c_type(o) for s, o in izip(self, other)
        )

    def __nonzero__(self):
        return 0

    @property
    def const(self):
        return True


class UserDefinedTypes(CType):
    def __init__(self, name, location):
        self._name = name
        super(UserDefinedTypes, self).__init__(location)

    @property
    def name(self):
        return self.__class__.get_name(self._name)

    @classmethod
    def get_name(cls, value):
        return (value and cls.__name__.split('Type')[0].lower() + ' ' + value) or value


no_default = object()


class CompositeType(UserDefinedTypes):
    supported_operations = {MEMBER_ACCESS_OPERATOR, TOKENS.EQUAL}

    def __init__(self, name, _members, location=LocationNotSet):
        self._members = None
        if _members is not None:
            self.members = _members
        super(CompositeType, self).__init__(name, location)

    def __call__(self, location):
        obj = self.__class__(self._name, self.members, location)
        obj._incomplete = incomplete(self)
        return obj

    def __contains__(self, item):
        return item in self.members

    def __iter__(self):
        return iter(self.members)

    def offset(self, member_name, default=no_default):
        if member_name not in self and default is no_default:
            raise ValueError('{l} member {n} not in ctype {c}'.format(l=loc(member_name), n=member_name, c=self))
        return self.offset_from_name.get(member_name, default)

    def member(self, member_name_or_offset, default=no_default):
        # if offset then get name ...
        if isinstance(member_name_or_offset, (int, long)) and member_name_or_offset < len(self.offset_from_name):
            member_name_or_offset = self.name_from_offset[member_name_or_offset]
        return self._members[member_name_or_offset] if default is no_default \
            else self._members.get(member_name_or_offset, no_default)

    @property
    def members(self):
        return self._members

    @members.setter
    def members(self, _members):
        if self.members is None:
            self._members = _members
            self.name_from_offset = dict(enumerate(imap(getattr, members(self), repeat('name'))))
            self.offset_from_name = dict(imap(reversed, self.name_from_offset.iteritems()))
        elif _members != self._members:
            raise TypeError('{l} {t} already has members'.format(t=self.__class__.__name__, l=loc(self)))


    @property
    def incomplete(self):
        return self.members is None

    def __nonzero__(self):
        return 1

    def __eq__(self, other):
        return self is other or (  # Composites are self referencing each other when nested, TODO: fix this!!!!
            super(CompositeType, self).__eq__(other)
            and len(self.members) == len(other.members)
            and not any(starmap(cmp, izip(self.members.itervalues(), other.members.itervalues())))
        )


class StructType(CompositeType):
    pass


class UnionType(CompositeType):
    def offset(self, member_name, default=no_default):
        return super(UnionType, self).offset(member_name, default) and 0  # return (0 or default) or 0 ...


class EnumType(StrictlySigned, IntegerType):
    pass


# check if one type could be coerce to another.
def safe_type_coercion(from_type, to_type):
    if isinstance(from_type, NumericType) and isinstance(to_type, NumericType):
        # if unsigned(from_type) != unsigned(to_type):
        #     logger.warning('{l} mixing unsigned and signed values'.format(l=loc(from_type)))
        return True
    if isinstance(from_type, VAListType) or isinstance(to_type, (VAListType, UnionType)):
        return True
    if isinstance(from_type, FunctionType) and isinstance(to_type, PointerType):
        to_type = c_type(to_type)
    return from_type == to_type


char_type = CharType()
short_type = ShortType()
integer_type = IntegerType()
long_type = LongType()

unsigned_char_type = CharType(unsigned=True)
unsigned_short_type = ShortType(unsigned=True)
unsigned_integer_type = IntegerType(unsigned=True)
unsigned_long_type = LongType(unsigned=True)

float_type = FloatType()
double_type = DoubleType()

logical_type = LongType(LongType())

void_pointer_type = PointerType(VoidType(LocationNotSet))
char_array_type = ArrayType(CharType(LocationNotSet), None)

# c_scalar_core_types = CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, EnumType, PointerType
kind_of_types = {NumericType, IntegralType, WidthType, CoreType}
scalar_types = set(ifilter(
    lambda cls: cls not in kind_of_types and issubclass(cls, NumericType),
    ifilter(inspect.isclass, imap(getattr, repeat(current_module), dir(current_module)))
))
integral_types, real_types = imap(
    set,
    imap(
        ifilter,
        imap(lambda cls_type: (lambda cls, cls_type=cls_type: issubclass(cls, cls_type)), (IntegralType, FloatType)),
        repeat(scalar_types)
    )
)


def base_c_type(ctype):
    if isinstance(ctype, FunctionType):
        return IntegralType
    assert isinstance(ctype, NumericType)
    if isinstance(ctype, IntegralType):
        return IntegralType
    return NumericType


def core_c_type(ctype):
    next_ctype = c_type(ctype)
    return ctype if type(next_ctype) is CType else core_c_type(next_ctype)


def set_core_type(top_type, bottom_type):
    # while type(c_type(base_type)) is not CType:
    #     base_type = c_type(base_type)
    core_c_type(top_type).c_type = bottom_type
    return top_type

type_property_names = 'c_type', 'unsigned', 'const', 'volatile', 'supported_operations', 'incomplete'
for _name in type_property_names:
    setattr(current_module, _name, get_attribute_func(_name))


def get_not_a_composite_func(ctype, default=no_default, name_or_offset=''):
    def not_a_composite(_name_or_offset=name_or_offset, _default=default, _ctype=ctype):
        if _default is not no_default:
            return _default
        raise ValueError('{l} ctype {c} is not a composite type'.format(l=loc(_name_or_offset), c=_ctype))
    return not_a_composite


def members(ctype, default=no_default):
    return getattr(
        getattr(ctype, 'members', get_not_a_composite_func(ctype, default)),
        'itervalues',
        lambda: default
    )()


def member(ctype, name_or_offset, default=no_default):
    return getattr(ctype, 'member', get_not_a_composite_func(ctype, default, name_or_offset))(name_or_offset, default)


def offset(ctype, name, default=no_default):
    return getattr(ctype, 'offset', get_not_a_composite_func(ctype))(name, default)


suggested_size_rules = {
    CharType: 1,
    ShortType: 2,
    IntegerType: 4,
    LongType: 8,
    PointerType: 8,

    FloatType: 4,
    DoubleType: 8
}


def suggested_size(ctype):  # TODO: find alternative!!!
    return suggested_size_rules[type(ctype)]