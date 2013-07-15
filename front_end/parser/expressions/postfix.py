__author__ = 'samyvilar'

from itertools import izip_longest
from sequences import peek, consume
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.types import c_type, FunctionType, PointerType, IntegralType, StructType, safe_type_coercion
from front_end.parser.ast.expressions import ArraySubscriptingExpression, ArgumentExpressionList, FunctionCallExpression
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression

from front_end.errors import error_if_not_type, error_if_not_value


# Subscript operator can only be called on an expression that returns a pointer type.
def subscript_oper(tokens, symbol_table, primary_exp, expression_func):
    location, _ = loc(consume(tokens)), error_if_not_type([c_type(primary_exp)], PointerType)
    exp = expression_func(tokens, symbol_table)
    # array subscripts must be of Integral Type.
    _, _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET), error_if_not_type([c_type(exp)], IntegralType)
    return ArraySubscriptingExpression(primary_exp, exp, c_type(c_type(primary_exp))(location), location)


# list of 1 or more expressions to be used as arguments to a function call.
def argument_expression_list(tokens, symbol_table, expression_func):
    # : expression (',' expression)*
    initial_argument = expression_func(tokens, symbol_table)
    expressions = ArgumentExpressionList([initial_argument], loc(initial_argument))
    while peek(tokens, default='') == TOKENS.COMMA:
        _ = consume(tokens)
        expressions.append(expression_func(tokens, symbol_table))
    return expressions


# Function call can only be called on an expression that return a pointer to a function type or a function_type.
def function_call(tokens, symbol_table, primary_exp, expression_func):
    if not isinstance(c_type(primary_exp), FunctionType) and \
       not (isinstance(c_type(primary_exp), PointerType) and isinstance(c_type(c_type(primary_exp)), FunctionType)):
        raise ValueError('{l} Expected a FunctionType or Pointer to FunctionType got {got}'.format(
            l=loc(peek(tokens)), got=c_type(primary_exp)
        ))
    l = loc(consume(tokens))

    if isinstance(c_type(primary_exp), FunctionType):
        func_type = c_type(primary_exp)
    else:
        func_type = c_type(c_type(primary_exp))
    assert isinstance(func_type, FunctionType)
    ret_type = c_type(func_type)

    # get expression arguments.
    expression_argument_list = ArgumentExpressionList((), l)
    if peek(tokens, default='') != TOKENS.RIGHT_PARENTHESIS:
        # check the arguments.
        for exp_type, arg in izip_longest(func_type, argument_expression_list(tokens, symbol_table, expression_func)):
            if arg is None:
                raise ValueError('{l} Function call with not enough arguments specified.'.format(l=l))
            elif exp_type is None:
                raise ValueError('{l} Function call with to many arguments specified'.format(l=loc(arg)))
            elif not safe_type_coercion(c_type(arg), c_type(exp_type)):
                raise ValueError('{l} Function call, could not coerce argument from {f_type} to {t_type}'.format(
                    l=loc(arg), f_type=c_type(arg), t_type=c_type(exp_type),
                ))
            expression_argument_list.append(arg)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    return FunctionCallExpression(primary_exp, expression_argument_list, ret_type(l), l)


def dot_oper(tokens, symbol_table, primary_exp, expression_func):
    location, _ = loc(consume(tokens)), error_if_not_type([c_type(primary_exp)], StructType)
    member = error_if_not_type(tokens, IDENTIFIER)
    if member not in c_type(primary_exp):
        raise ValueError('{l} struct does not contain member {member}'.format(member=member, l=loc(member)))
    return ElementSelectionExpression(
        primary_exp, member, c_type(c_type(primary_exp).members[member])(loc(member)), loc(member)
    )


def arrow_operator(tokens, symbol_table, primary_exp, expression_func):
    location, _ = loc(consume(tokens)), error_if_not_type([c_type(primary_exp)], PointerType)
    _, member = error_if_not_type([c_type(c_type(primary_exp))], StructType), error_if_not_type(tokens, IDENTIFIER)

    if member not in c_type(c_type(primary_exp)):
        raise ValueError('{l} pointer to struct which does not contain member {member}'.format(
            member=member, l=loc(member)
        ))
    return ElementSelectionThroughPointerExpression(
        primary_exp, member, c_type(c_type(c_type(primary_exp)).members[member])(loc(member)), loc(member)
    )


def inc_dec(tokens, symbol_table, primary_exp, expression_func):  # Postfix unary operators ++, --
    return inc_dec.rules[peek(tokens)](consume(tokens), primary_exp)
inc_dec.rules = {
    TOKENS.PLUS_PLUS: lambda t, primary_exp: PostfixIncrementExpression(
        primary_exp, c_type(primary_exp)(loc(t)), loc(t)
    ),
    TOKENS.MINUS_MINUS: lambda t, primary_exp: PostfixDecrementExpression(
        primary_exp, c_type(primary_exp)(loc(t)), loc(t)
    ),
}