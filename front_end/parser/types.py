__author__ = 'samyvilar'

from copy import deepcopy
from collections import OrderedDict
from itertools import izip

from logging_config import logging

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS


logger = logging.getLogger('parser')


class CType(object):
    rank = 0
    supported_operations = set()

    def __init__(self, location):
        self.location = location

    @property
    def c_type(self):
        return self

    @c_type.setter
    def c_type(self, _c_type):
        raise TypeError('{l} {c_type} is not a chained type, chained {to}'.format(c_type=self, to=_c_type, l=loc(self)))

    @property
    def unsigned(self):
        raise TypeError('{l} {ctype} does not support signed/unsigned'.format(l=loc(self), ctype=self))

    @property
    def incomplete(self):
        return True

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


class VoidType(ConcreteType):
    pass

LOGICAL_OPERATIONS = {
    TOKENS.EXCLAMATION,
    TOKENS.GREATER_THAN, TOKENS.LESS_THAN,
    TOKENS.EQUAL_EQUAL, TOKENS.NOT_EQUAL, TOKENS.GREATER_THAN_OR_EQUAL, TOKENS.LESS_THAN_OR_EQUAL,
}

ARITHMETIC_OPERATIONS = {TOKENS.PLUS, TOKENS.MINUS, TOKENS.STAR, TOKENS.FORWARD_SLASH}
COMPOUND_ARITHMETIC_OPERATIONS = {TOKENS.PLUS_EQUAL, TOKENS.MINUS_EQUAL, TOKENS.STAR_EQUAL, TOKENS.FORWARD_SLASH}
BITWISE_OPERATIONS = {
    TOKENS.TILDE,
    TOKENS.AMPERSAND, TOKENS.BAR, TOKENS.CARET, TOKENS.PERCENTAGE, TOKENS.SHIFT_LEFT, TOKENS.SHIFT_RIGHT,
}
BITWISE_COMPOUND_OPERATION = {
    TOKENS.AMPERSAND_EQUAL, TOKENS.BAR_EQUAL, TOKENS.CARET_EQUAL, TOKENS.SHIFT_LEFT_EQUAL, TOKENS.SHIFT_RIGHT_EQUAL,
}


class NumericType(ConcreteType):
    supported_operations = LOGICAL_OPERATIONS | ARITHMETIC_OPERATIONS


class IntegralType(NumericType):  # Integral types support all the same as Numeric including bitwise operation.
    supported_operations = NumericType.supported_operations | BITWISE_OPERATIONS

    def __init__(self, location, unsigned=False):
        self._unsigned = unsigned
        super(IntegralType, self).__init__(location)

    def check_sign(self, other):
        if unsigned(self) != unsigned(other):
            logger.warning('{l} Comparing types with different signs'.format(l=loc(other)))

    def __gt__(self, other):
        self.check_sign(other)
        if self.rank == other.rank and unsigned(self) != unsigned(other):  # same rank but diff sign
            return unsigned(self)
        return super(IntegralType, self).__gt__(other)

    def __lt__(self, other):
        self.check_sign(other)
        if self.rank == other.rank and unsigned(self) != unsigned(other):  # same rank but diff sign
            return not unsigned(self)
        return super(IntegralType, self).__lt__(other)

    def __call__(self, location):
        return self.__class__(location, unsigned=unsigned(self))

    @property
    def unsigned(self):
        return self._unsigned


class CharType(IntegralType):
    rank = 1


class ShortType(IntegralType):
    rank = 2


class IntegerType(IntegralType):
    rank = 3


class LongType(IntegralType):
    rank = 4


class FloatType(NumericType):
    rank = 5

    @property
    def unsigned(self):
        return False


class DoubleType(FloatType):
    rank = 6


class ChainedType(CType):
    def __init__(self, ctype, location):
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
        return all((super(ChainedType, self).__eq__(other), c_type(self) == c_type(other)))


    @property
    def incomplete(self):
        return incomplete(c_type(self))


class PointerType(ChainedType, IntegralType):
    rank = 4
    supported_operations = LOGICAL_OPERATIONS | {TOKENS.PLUS,  TOKENS.MINUS}

    def __call__(self, location):
        return self.__class__(c_type(self)(location), location)

    def __repr__(self):
        return 'Pointer to {to}'.format(to=c_type(self))

    @property
    def unsigned(self):
        return True

    def __nonzero__(self):
        return bool(c_type(self))


class ArrayType(PointerType):
    def __init__(self, __c_type, length, location):
        self.length = length
        super(ArrayType, self).__init__(__c_type, location)

    def __call__(self, location):
        return self.__class__(c_type(self)(location), len(self), location)

    def __len__(self):
        return self.length

    def __repr__(self):
        return "Array of {of}".format(of=self.c_type)


class StringType(ArrayType):
    def __init__(self, length, location):
        super(StringType, self).__init__(CharType(location), length, location)


class FunctionType(ChainedType, list):
    def __init__(self, ctype, arguments, location):
        super(FunctionType, self).__init__(ctype, location)
        list.__init__(self, arguments or ())

    def __repr__(self):
        return 'FunctionType returning {c_type} accepting ({arguments})'.format(
            c_type=c_type(self), arguments=''.join(repr(arg) + ', ' for arg in self),
        )

    def __eq__(self, other):
        return all((
            super(FunctionType, self).__eq__(other),
            len(self) == len(other),
            all(c_type(s) == c_type(o) for s, o in izip(self, other))
        ))


class StructType(CType):
    def __init__(self, name, members, location):
        self._name, self._members = name or '', members
        super(StructType, self).__init__(location)

    def __call__(self, location):
        struct = StructType(self._name, self.members, location)
        struct._incomplete = incomplete(self)
        return struct

    def __contains__(self, item):
        return item in self.members

    def __iter__(self):
        return iter(self.members)

    @property
    def members(self):
        return self._members

    @members.setter
    def members(self, _members):
        if self.members is None:
            self._members = _members
        else:
            raise TypeError('{l} StructType already has members'.format(l=loc(self)))

    @property
    def incomplete(self):
        return self.members is None

    @property
    def name(self):
        return StructType.get_name(self._name)

    @staticmethod
    def get_name(value):
        return (value and 'struct ' + value) or value

    def __nonzero__(self):
        return 1

    def __eq__(self, other):
        return all((
            super(StructType, self).__eq__(other),
            len(self.members) == len(other.members),
            all(member == other_member for member, other_member in izip(
                self.members.itervalues(), other.members.itervalues())),
        ))


# check if one type could be coerce to another.
def safe_type_coercion(from_type, to_type):
    if isinstance(from_type, NumericType) and isinstance(to_type, NumericType):
        if unsigned(from_type) != unsigned(to_type):
            logger.warning('{l} mixing unsigned and signed values'.format(l=loc(from_type)))
        return True
    return from_type == to_type


def c_type(obj, *args):
    if args:
        return getattr(obj, 'c_type', args[0])
    else:
        return getattr(obj, 'c_type')


def base_c_type(ctype):
    assert isinstance(ctype, NumericType)
    if isinstance(c_type(ctype), PointerType):
        return PointerType
    if isinstance(c_type(ctype), IntegralType):
        return IntegralType
    return NumericType


def incomplete(obj):
    return getattr(obj, 'incomplete')


def unsigned(obj):
    return getattr(obj, 'unsigned')


def set_core_type(base_type, fundamental_type):
    while type(c_type(base_type)) is not CType:
        base_type = c_type(base_type)
    base_type.c_type = fundamental_type