__author__ = 'samyvilar'

from itertools import izip

from utils import get_attribute_func
from front_end.loader.locations import loc, LocationNotSet
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.general import Node, EmptyNode
from front_end.parser.types import CType, IntegerType, IntegralType, c_type, safe_type_coercion, unsigned
from front_end.parser.types import ArrayType, StructType, NumericType, PointerType


from front_end.errors import error_if_not_type
from collections import OrderedDict


class TypedNode(Node):
    def __init__(self, ctype, location=LocationNotSet):
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
        return all((super(Expression, self).__eq__(other), lvalue(self, False) == lvalue(other, False)))


class ExpressionNode(Expression):
    def __init__(self, exp, ctype, location=LocationNotSet):
        self.exp = exp
        super(ExpressionNode, self).__init__(ctype, location)

    def __eq__(self, other):
        return all((super(ExpressionNode, self).__eq__(other), exp(self) == exp(other)))


class OperatorNode(ExpressionNode):
    def __init__(self, oper, exp, ctype, location=LocationNotSet):
        self.oper = oper
        super(OperatorNode, self).__init__(exp, ctype, location)

    def __eq__(self, other):
        return all((super(OperatorNode, self).__eq__(other), oper(self) == oper(other)))


class CommaExpression(OperatorNode):
    def __init__(self, expressions, ctype, location=LocationNotSet):
        super(CommaExpression, self).__init__(TOKENS.COMMA, expressions, ctype, location)


class LiteralExpression(ExpressionNode):
    pass


def defaults(ctype, designations=None):
    designations = designations or OrderedDict()
    if isinstance(ctype, NumericType):
        designations[0] = ConstantExpression(0, ctype(loc(ctype)), loc(ctype))
    elif isinstance(ctype, ArrayType):
        for index in xrange(len(ctype)):
            designations[index] = defaults(c_type(ctype))
    elif isinstance(ctype, StructType):
        for offset, member_name in enumerate(ctype.members):
            designations[offset] = defaults(c_type(ctype.members[member_name]))
    else:
        raise ValueError('{l} Unable to generate default expression for ctype {c}'.format(l=loc(ctype), c=ctype))
    return designations


class ConstantExpression(ExpressionNode):
    pass


class EmptyExpression(ConstantExpression, EmptyNode):
    def __init__(self, ctype=CType(), location=LocationNotSet):
        super(EmptyExpression, self).__init__(0, ctype(location), location)

    def __eq__(self, other):
        return isinstance(other, EmptyExpression)


class TrueExpression(ConstantExpression):
    def __init__(self, location=LocationNotSet):
        super(TrueExpression, self).__init__(True, IntegerType(location), location)


class FalseExpression(ConstantExpression):
    def __init__(self, location=LocationNotSet):
        super(FalseExpression, self).__init__(False, IntegerType(location), location)


class IdentifierExpression(ExpressionNode):
    def __init__(self, name, ctype, location=LocationNotSet):
        self.name, self.lvalue = name, lvalue(ctype, False)
        super(IdentifierExpression, self).__init__(name, ctype, location)


class UnaryExpression(OperatorNode):
    pass


class AddressOfExpression(UnaryExpression):
    def __init__(self, exp, ctype, location=LocationNotSet):
        # error_if_not_addressable(exp)  TODO: implement.
        super(AddressOfExpression, self).__init__(TOKENS.AMPERSAND, exp, ctype, location)


class SizeOfExpression(UnaryExpression):
    def __init__(self, exp, location=LocationNotSet):
        super(SizeOfExpression, self).__init__(TOKENS.SIZEOF, exp, IntegerType(location, unsigned=True), location)


class CastExpression(UnaryExpression):
    def __init__(self, exp, ctype, location=LocationNotSet):
        super(CastExpression, self).__init__('__CAST__', exp, ctype, location)


class BinaryExpression(OperatorNode):
    def __init__(self, left_exp, oper, right_exp, ctype, location=LocationNotSet):
        self.left_exp, self.right_exp = left_exp, right_exp
        super(BinaryExpression, self).__init__(oper, self, ctype, location)

    def __eq__(self, other):
        return all((
            super(BinaryExpression, self).__eq__(other),
            right_exp(self) == right_exp(other),
            left_exp(self) == left_exp(other),
        ))


class TernaryExpression(OperatorNode):
    def __init__(self, conditional_exp, if_true_exp, if_false_exp, ctype, location=LocationNotSet):
        self.left_exp = if_true_exp
        self.right_exp = if_false_exp
        super(TernaryExpression, self).__init__(TOKENS.QUESTION + TOKENS.COLON, conditional_exp, ctype, location)

    def __eq__(self, other):
        return all((
            super(TernaryExpression, self).__eq__(other),
            exp(self) == exp(other),
            left_exp(self) == left_exp(other),
            right_exp(self) == right_exp(other),
        ))


class AssignmentExpression(BinaryExpression):
    def __init__(self, left_exp, operator, right_exp, ctype, location=LocationNotSet):
        # error_if_not_assignable(left_exp, location) TODO: implement.
        if not safe_type_coercion(c_type(left_exp), c_type(right_exp)):
            raise ValueError('{l} Cannot assign from type {from_type} to {to_type}'.format(
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
    def __init__(self, exp, ctype, location=LocationNotSet):
        self.lvalue = lvalue(ctype, False)
        super(DereferenceExpression, self).__init__(TOKENS.STAR, exp, ctype, location)


class ArraySubscriptingExpression(PostfixExpression):
    def __init__(self, primary_exp, subscript_expression, ctype, location=LocationNotSet):
        self.lvalue = lvalue(ctype, False)
        super(ArraySubscriptingExpression, self).__init__(
            primary_exp,
            TOKENS.LEFT_BRACKET + TOKENS.RIGHT_BRACKET,
            subscript_expression,
            ctype,
            location
        )


class ArgumentExpressionList(Node, list):
    def __init__(self, argument_expressions, location=LocationNotSet):
        super(ArgumentExpressionList, self).__init__(location)
        list.__init__(self, argument_expressions or ())

    def __eq__(self, other):
        return all((len(self) == len(other), all(c_type(s_arg) == c_type(o_arg) for s_arg, o_arg in izip(self, other))))


class FunctionCallExpression(PostfixExpression):
    def __init__(self, primary_exp, argument_expression_list, ctype, location=LocationNotSet):
        super(FunctionCallExpression, self).__init__(primary_exp, 'func()', argument_expression_list, ctype, location)


class ElementSelection(PostfixExpression):
    def __init__(self, primary_exp, oper, member, ctype, location=LocationNotSet):
        self.lvalue = lvalue(ctype, False)
        super(ElementSelection, self).__init__(primary_exp, oper, member, ctype, location)


class ElementSelectionExpression(ElementSelection):
    def __init__(self, primary_exp, member, ctype, location=LocationNotSet):
        super(ElementSelectionExpression, self).__init__(primary_exp, TOKENS.DOT, member, ctype, location)


class ElementSelectionThroughPointerExpression(ElementSelection):
    def __init__(self, primary_exp, member, ctype, location=LocationNotSet):
        super(ElementSelectionThroughPointerExpression, self).__init__(
            primary_exp, TOKENS.ARROW, member, ctype, location
        )


class CompoundLiteral(PostfixExpression, list):
    def __init__(self, expr, ctype, location=LocationNotSet):
        super(CompoundLiteral, self).__init__(ctype, '(TYPE_NAME *)initializer_list', expr, ctype, location)
        list.__init__(self, expr)


class IntegralExpression(TypedNode):
    def __init__(self, ctype, location):
        error_if_not_type(ctype, IntegralType)
        super(IntegralExpression, self).__init__(ctype, location)


class IncDecExpr(CompoundAssignmentExpression, IntegralExpression):
    def __init__(self, exp, operator, ctype, location=LocationNotSet):
        super(IncDecExpr, self).__init__(
            exp,
            operator,
            ConstantExpression(1, IntegerType(location, unsigned=unsigned(ctype)), location),
            ctype,
            location
        )
        ExpressionNode.__init__(self, exp, ctype, location)  # CompoundAssignment uses itself as exp


class IncrementExpression(IncDecExpr):  # Statement/Expression
    def __init__(self, exp, ctype, location=LocationNotSet):
        super(IncrementExpression, self).__init__(exp, TOKENS.PLUS_EQUAL, ctype, location)


class DecrementExpression(IncDecExpr):
    def __init__(self, exp, ctype, location=LocationNotSet):
        super(DecrementExpression, self).__init__(exp, TOKENS.MINUS_EQUAL, ctype, location)


class PrefixIncrementExpression(IncrementExpression):
    pass


class PostfixIncrementExpression(IncrementExpression):
    pass


class PrefixDecrementExpression(DecrementExpression):
    pass


class PostfixDecrementExpression(DecrementExpression):
    pass


oper = get_attribute_func('oper')
exp = get_attribute_func('exp')
lvalue = get_attribute_func('lvalue')
right_exp = get_attribute_func('right_exp')
left_exp = get_attribute_func('left_exp')