__author__ = 'samyvilar'

from front_end.loader.locations import loc

from front_end.parser.types import CType, c_type, safe_type_coercion, FunctionType
from front_end.parser.ast.general import Node, EmptyNode
from front_end.parser.ast.expressions import EmptyExpression, ConstantExpression, TypedNode

from front_end.errors import error_if_not_type


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
    def __init__(self, name, ctype, location, _storage_class=None):
        self.name = name
        if isinstance(ctype, FunctionType) and isinstance(_storage_class, Static):
            raise ValueError()
        self.storage_class = _storage_class or (Extern(location) if isinstance(ctype, FunctionType) else _storage_class)
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
    def __init__(self, name, ctype, initialization, location, storage_class):
        self._initialization = initialization
        super(Definition, self).__init__(name, ctype, location, storage_class)

    @property
    def initialization(self):
        return self._initialization

    @initialization.setter
    def initialization(self, value):
        if value and c_type(self) and not safe_type_coercion(c_type(self), c_type(value)):
            raise ValueError('{l} Could not coerce types from {from_type} to {to_type}'.format(
                from_type=c_type(value), to_type=c_type(self)
            ))
        if isinstance(self.storage_class, (Static, Extern)) \
           and not isinstance(value, (ConstantExpression, EmptyExpression)):
            raise ValueError('{l} Static definition may only be initialized with constant expressions'.format(
                l=loc(value)
            ))
        self._initialization = value

    def __eq__(self, other):
        return all((super(Definition, self).__eq__(other), initialization(self) == initialization(other)))

    def __repr__(self):
        return 'Definition of {n} type {ctype}'.format(n=name(self), ctype=c_type(self))


class FunctionDefinition(Definition, list):
    def __init__(self, c_decl, body, location, storage_class):
        _ = error_if_not_type([c_type(c_decl)], FunctionType)
        if not all(isinstance(arg, Declarator) for arg in c_type(c_decl)):
            raise ValueError('{l} Function definition must have concrete declarators.'.format(l=loc(c_type(c_decl))))
        super(FunctionDefinition, self).__init__(name(c_decl), c_type(c_decl), body, location, storage_class)
        list.__init__(self, body)

    def check_return_stmnt(self, return_exp):
        if not safe_type_coercion(c_type(return_exp),  c_type(c_type(self))):
            raise ValueError('{l} Return expression {ret_type} cannot be coerce to func return type {exp_type}'.format(
                l=loc(return_exp), ret_type=c_type(return_exp), exp_type=c_type(c_type(self))
            ))


class TypeDef(Definition, StorageClass):
    def __init__(self, name, c_type, location):
        super(TypeDef, self).__init__(name, c_type, None, location, self)

    def __call__(self, location):
        return c_type(self)(location)


class EmptyDeclaration(EmptyNode, Declaration):
    c_type = CType

    def __init__(self, location):
        super(EmptyDeclaration, self).__init__(location)


class Declarator(TypedNode):
    def __init__(self, name, c_type, initialization, location):
        self.name, self.initialization = name, initialization
        super(Declarator, self).__init__(c_type, location)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not name:
            raise ValueError('{l} Declarator names cannot be empty, got "{got}"'.format(l=loc(value), got=value))
        self._name = value


class AbstractDeclarator(TypedNode):
    @property
    def name(self):
        raise TypeError

    @name.setter
    def name(self, value):
        raise TypeError


def name(obj):
    return getattr(obj, 'name', '')


def initialization(obj):
    return getattr(obj, 'initialization', EmptyExpression())