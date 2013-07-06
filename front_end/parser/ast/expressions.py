__author__ = 'samyvilar'

from itertools import izip

from front_end.loader.locations import LocationNotSet
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.general import Node, EmptyNode
from front_end.parser.types import CType, IntegerType, IntegralType, c_type, safe_type_coercion

from front_end.errors import error_if_not_addressable, error_if_not_assignable, error_if_not_type


class TypedNode(Node):
    def __init__(self, ctype, location):
        self.ctype = ctype
        super(TypedNode, self).__init__(location)

    @property
    def c_type(self):
        return self.ctype

    @c_type.setter
    def c_type(self, value):
        if not c_type(self):
            self.ctype = value
        else:
            raise ValueError

    def __eq__(self, other):
        return all((super(TypedNode, self).__eq__(other), c_type(self) == c_type(other)))


class Expression(TypedNode):
    def __eq__(self, other):
        return all((super(Expression, self).__eq__(other), lvalue(self) == lvalue(other)))


class ExpressionNode(Expression):
    def __init__(self, exp, ctype, location):
        self.exp = exp
        super(ExpressionNode, self).__init__(ctype, location)

    def __eq__(self, other):
        return all((super(ExpressionNode, self).__eq__(other), exp(self) == exp(other)))


class OperatorNode(ExpressionNode):
    def __init__(self, oper, exp, ctype, location):
        self.oper = oper
        super(OperatorNode, self).__init__(exp, ctype, location)

    def __eq__(self, other):
        return all((super(OperatorNode, self).__eq__(other), oper(self) == oper(other)))


class ConstantExpression(ExpressionNode):
    pass


class EmptyExpression(ConstantExpression, EmptyNode):
    def __init__(self, ctype=CType(LocationNotSet), location=LocationNotSet):
        super(EmptyExpression, self).__init__(0, ctype(location), location)

    def __eq__(self, other):
        return isinstance(other, EmptyExpression)


class TrueExpression(ConstantExpression):
    def __init__(self, location):
        super(TrueExpression, self).__init__(True, IntegerType(location), location)


class FalseExpression(ConstantExpression):
    def __init__(self, location):
        super(FalseExpression, self).__init__(False, IntegerType(location), location)


class IdentifierExpression(ExpressionNode):
    def __init__(self, name, ctype, location):
        self.name, self.lvalue = name, lvalue(ctype)
        super(IdentifierExpression, self).__init__(name, ctype, location)


class UnaryExpression(OperatorNode):
    def __init__(self, oper, exp, ctype, location):
        super(UnaryExpression, self).__init__(oper, exp, ctype, location)


class AddressOfExpression(UnaryExpression):
    def __init__(self, exp, ctype, location):
        # error_if_not_addressable(exp)  TODO: implement.
        super(AddressOfExpression, self).__init__(TOKENS.AMPERSAND, exp, ctype, location)


class SizeOfExpression(UnaryExpression):
    def __init__(self, exp, location):
        super(SizeOfExpression, self).__init__(TOKENS.SIZEOF, exp, IntegerType(location), location)


class CastExpression(UnaryExpression):
    def __init__(self, exp, ctype, location):
        super(CastExpression, self).__init__('__CAST__', exp, ctype, location)


class BinaryExpression(OperatorNode):
    def __init__(self, left_exp, oper, right_exp, ctype, location):
        self.left_exp, self.right_exp = left_exp, right_exp
        super(BinaryExpression, self).__init__(oper, self, ctype, location)

    def __eq__(self, other):
        return all((
            super(BinaryExpression, self).__eq__(other),
            right_exp(self) == right_exp(other),
            left_exp(self) == left_exp(other),
        ))


class AssignmentExpression(BinaryExpression):
    def __init__(self, left_exp, operator, right_exp, ctype, location):
        # error_if_not_assignable(left_exp, location) TODO: implement.
        if not safe_type_coercion(c_type(left_exp), c_type(right_exp)):
            raise ValueError('{l} Cannot assign incompatible types {to_type} {from_type}'.format(
                l=location, from_type=c_type(right_exp), to_type=c_type(left_exp),
            ))
        super(AssignmentExpression, self).__init__(left_exp, operator, right_exp, ctype, location)


class CompoundAssignmentExpression(AssignmentExpression):
    pass


class PostfixExpression(BinaryExpression):
    pass


class PrefixExpression(UnaryExpression):
    pass


class DereferenceExpression(PrefixExpression):
    def __init__(self, exp, ctype, location):
        self.lvalue = lvalue(ctype)
        super(DereferenceExpression, self).__init__(TOKENS.STAR, exp, ctype, location)


class ArraySubscriptingExpression(PostfixExpression):
    def __init__(self, primary_exp, subscript_expression, ctype, location):
        self.lvalue = lvalue(ctype)
        super(ArraySubscriptingExpression, self).__init__(
            primary_exp,
            TOKENS.LEFT_BRACKET + TOKENS.RIGHT_BRACKET,
            subscript_expression,
            ctype,
            location
        )


class ArgumentExpressionList(Node, list):
    def __init__(self, argument_expressions, location):
        super(ArgumentExpressionList, self).__init__(location)
        list.__init__(self, argument_expressions or ())

    def __eq__(self, other):
        return all((len(self) == len(other), all(c_type(s_arg) == c_type(o_arg) for s_arg, o_arg in izip(self, other))))


class FunctionCallExpression(PostfixExpression):
    def __init__(self, primary_exp, argument_expression_list, ctype, location):
        super(FunctionCallExpression, self).__init__(primary_exp, 'func()', argument_expression_list, ctype, location)


class ElementSelection(PostfixExpression):
    def __init__(self, primary_exp, oper, member, ctype, location):
        self.lvalue = lvalue(ctype)
        super(ElementSelection, self).__init__(primary_exp, oper, member, ctype, location)


class ElementSelectionExpression(ElementSelection):
    def __init__(self, primary_exp, member, ctype, location):
        super(ElementSelectionExpression, self).__init__(primary_exp, TOKENS.DOT, member, ctype, location)


class ElementSelectionThroughPointerExpression(ElementSelection):
    def __init__(self, primary_exp, member, ctype, location):
        super(ElementSelectionThroughPointerExpression, self).__init__(
            primary_exp, TOKENS.ARROW, member, ctype, location
        )


class IntegralExpression(TypedNode):
    def __init__(self, ctype, location):
        error_if_not_type([ctype], IntegralType, location)
        super(IntegralExpression, self).__init__(ctype, location)


class IncrementExpression(CompoundAssignmentExpression, IntegralExpression):  # Statement/Expression
    def __init__(self, exp, ctype, location):
        super(IncrementExpression, self).__init__(
            exp,
            TOKENS.PLUS_EQUAL,
            ConstantExpression(1, IntegerType(location), location),
            ctype,
            location
        )
        ExpressionNode.__init__(self, exp, ctype, location)  # CompoundAssignment uses itself as exp


class DecrementExpression(CompoundAssignmentExpression, IntegralExpression):
    def __init__(self, exp, ctype, location):
        super(DecrementExpression, self).__init__(
            exp,
            TOKENS.MINUS_EQUAL,
            ConstantExpression(1, IntegerType(location), location),
            ctype,
            location
        )
        ExpressionNode.__init__(self, exp, ctype, location)


class PrefixIncrementExpression(IncrementExpression):
    pass


class PostfixIncrementExpression(IncrementExpression):
    pass


class PrefixDecrementExpression(DecrementExpression):
    pass


class PostfixDecrementExpression(DecrementExpression):
    pass


def oper(exp):
    return getattr(exp, 'oper')


def exp(exp):
    return getattr(exp, 'exp')


def lvalue(exp):
    return getattr(exp, 'lvalue', False)


def right_exp(exp):
    return getattr(exp, 'right_exp')


def left_exp(exp):
    return getattr(exp, 'left_exp')


def assignable(exp):
    return lvalue()