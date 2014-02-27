__author__ = 'samyvilar'

from front_end.loader.locations import loc, LocationNotSet

from utils import get_attribute_func
from front_end.parser.types import CType, c_type, safe_type_coercion, ArrayType
from front_end.parser.ast.general import Node, EmptyNode

from front_end.parser.ast.expressions import TypedNode
from front_end.parser.ast.expressions import ConstantExpression, CompoundLiteral, Initializer, EmptyExpression

from utils.errors import error_if_not_type, raise_error


# class Designation(Node):
#     pass
#
#
# class Identifier(Designation):
#     pass
#
#
# class Range(Designation):
#     pass


class StorageClass(Node):
    def __str__(self):
        return self.__class__.__name__


class Auto(StorageClass):
    pass


class Register(StorageClass):
    pass


class Extern(StorageClass):
    pass


class Static(StorageClass):
    pass


class Declaration(TypedNode):
    def __init__(self, name, ctype, location=LocationNotSet, _storage_class=None):
        self.name = name
        self.storage_class = _storage_class
        super(Declaration, self).__init__(ctype, location)

    def __eq__(self, other):
        return all((
            super(Declaration, self).__eq__(other),
            name(self) == name(other),
            self.storage_class == other.storage_class
        ))

    def __repr__(self):
        return 'Declaration {name} of {c_type}'.format(name=name(self), c_type=c_type(self))


class Definition(Declaration):
    def __init__(self, name, ctype, initialization, location=LocationNotSet, storage_class=None):
        self._initialization = initialization
        super(Definition, self).__init__(name, ctype, location, storage_class)

    @property
    def initialization(self):
        return self._initialization

    @initialization.setter
    def initialization(self, value):
        _ = value and c_type(self) and not safe_type_coercion(c_type(self), c_type(value)) and raise_error(
            '{l} Could not coerce types from {from_type} to {to_type}'.format(
                l=loc(self), from_type=c_type(value), to_type=c_type(self)
            ))

        if isinstance(c_type(self), ArrayType):
            _ = error_if_not_type(value, (ConstantExpression, CompoundLiteral, Initializer, EmptyExpression))
            if c_type(self).length is None and isinstance(value, (Initializer, CompoundLiteral)):
                c_type(self).length = len(value)
        self._initialization = value

    def __eq__(self, other):
        return all((super(Definition, self).__eq__(other), initialization(self) == initialization(other)))

    def __repr__(self):
        return 'Definition of {n} type {ctype}'.format(n=name(self), ctype=c_type(self))


class TypeDef(Definition, StorageClass):
    def __init__(self, name, c_type, location=LocationNotSet):
        super(TypeDef, self).__init__(name, c_type, None, location, self)

    def __call__(self, location):
        return c_type(self)(location)


class EmptyDeclaration(Declaration, EmptyNode):
    def __init__(self, location, storage_class):
        super(EmptyDeclaration, self).__init__('', CType(location), location, storage_class)


class Declarator(TypedNode):
    def __init__(self, name, ctype, initialization, location=LocationNotSet):
        self.name, self.initialization = name, initialization
        super(Declarator, self).__init__(ctype, location)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value:
            raise ValueError('{l} Declarator names cannot be empty, got "{got}"'.format(l=loc(value), got=value))
        self._name = value


class AbstractDeclarator(TypedNode):
    pass


name = get_attribute_func('name')
initialization = get_attribute_func('initialization')