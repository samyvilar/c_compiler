__author__ = 'samyvilar'

from itertools import izip, imap
from collections import Iterable

from logging_config import logging

from front_end.loader.locations import loc, LocationNotSet
from front_end.tokenizer.tokens import TOKENS


logger = logging.getLogger('parser')


class CType(object):
    rank = 0
    supported_operations = set()

    def __init__(self, location=LocationNotSet):
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
MEMBER_ACCESS_THROUGH_POINTER = TOKENS.ARROW


class NumericType(ConcreteType):
    supported_operations = LOGICAL_OPERATIONS | ARITHMETIC_OPERATIONS | COMPOUND_OPERATIONS  # TODO check for lvalue


class IntegralType(NumericType):  # Integral types support all the same as Numeric including bitwise operation.
    supported_operations = NumericType.supported_operations | BITWISE_OPERATIONS

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


class CharType(IntegralType):
    rank = 1


class IntegerType(IntegralType):
    rank = 4


class FloatType(NumericType):
    rank = 5

    @property
    def unsigned(self):
        return False


class DoubleType(FloatType):
    rank = 8


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


class VAListType(CType):
    pass


class WidthType(ChainedType, IntegralType):
    incomplete = False

    def __init__(self, ctype=None, location=LocationNotSet, unsigned=False):
        ctype = ctype or IntegerType(location, unsigned=unsigned)
        super(WidthType, self).__init__(ctype, location)
        self.unsigned = unsigned

    def __call__(self, location):
        return self.__class__(c_type(self)(location), location, unsigned=self.unsigned)

    @property
    def rank(self):
        return c_type(self).rank


class LongType(WidthType):
    rank = 4
    pass


class ShortType(WidthType):
    rank = 2
    pass


class PointerType(ChainedType, IntegralType):
    rank = 4
    supported_operations = LOGICAL_OPERATIONS | {
        TOKENS.PLUS,  TOKENS.MINUS, TOKENS.PLUS_EQUAL, TOKENS.MINUS_EQUAL, SUBSCRIPT_OPERATOR
    }

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


class StringType(ArrayType):
    def __init__(self, length, location=LocationNotSet):
        super(StringType, self).__init__(CharType(location), length, location)


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

    @property
    def const(self):
        return True


class StructType(CType):
    supported_operations = {MEMBER_ACCESS_OPERATOR, TOKENS.EQUAL}

    def __init__(self, name, members, location=LocationNotSet):
        self._name, self._members = name or '', members
        if isinstance(members, Iterable):
            self._offsets = dict(imap(reversed, enumerate(members)))
        else:
            self._offsets = None
        super(StructType, self).__init__(location)

    def __call__(self, location):
        struct = StructType(self._name, self.members, location)
        struct._incomplete = incomplete(self)
        return struct

    def __contains__(self, item):
        return item in self.members

    def __iter__(self):
        return iter(self.members)

    def offset(self, member_name):
        return self._offsets[member_name]

    @property
    def members(self):
        return self._members

    @members.setter
    def members(self, _members):
        if self.members is None:
            self._members = _members
            self._offsets = dict(imap(reversed, enumerate(_members)))
        elif _members != self._members:
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
        return self is other or (  # Structs are self referencing each other when nested, TODO: fix this!!!!
            super(StructType, self).__eq__(other) and
            len(self.members) == len(other.members) and
            all(member == other_member for member, other_member in izip(
                self.members.itervalues(), other.members.itervalues()))
        )


class UnionType(StructType):
    @property
    def name(self):
        return UnionType.get_name(self._name)

    @staticmethod
    def get_name(value):
        return (value and 'union ' + value) or value


# check if one type could be coerce to another.
def safe_type_coercion(from_type, to_type):
    if isinstance(from_type, NumericType) and isinstance(to_type, NumericType):
        # if unsigned(from_type) != unsigned(to_type):
        #     logger.warning('{l} mixing unsigned and signed values'.format(l=loc(from_type)))
        return True
    if isinstance(from_type, VAListType) or isinstance(to_type, VAListType):
        return True
    return from_type == to_type


__required__ = object()


def c_type(obj, argument=__required__):
    return getattr(obj, 'c_type') if argument is __required__ else getattr(obj, 'c_type')


def base_c_type(ctype):
    assert isinstance(ctype, NumericType)
    if isinstance(ctype, IntegralType):
        return IntegralType
    return NumericType


def incomplete(obj):
    return getattr(obj, 'incomplete')


def unsigned(obj):
    return getattr(obj, 'unsigned')


def const(obj, argument=__required__):
    return getattr(obj, 'const') if argument is __required__ else getattr(obj, 'const', False)


def volatile(obj, argument=__required__):
    return getattr(obj, 'volatile') if argument is __required__ else getattr(obj, 'volatile', argument)


def set_core_type(base_type, fundamental_type):
    while type(c_type(base_type)) is not CType:
        base_type = c_type(base_type)
    base_type.c_type = fundamental_type


def supported_operators(ctype):
    return ctype.supported_operations

unsigned_char_type = CharType(unsigned=True)
char_type = CharType()
unsigned_short = ShortType(unsigned=True)
short_type = ShortType()
integer_type = IntegerType()
unsigned_integer_type = IntegerType(unsigned=True)
unsigned_long_type = LongType(unsigned=True)
long_type = LongType()
float_type = FloatType()
double_type = DoubleType()

void_pointer_type = PointerType(VoidType(LocationNotSet), LocationNotSet)
char_array_type = ArrayType(CharType(LocationNotSet), None, LocationNotSet)