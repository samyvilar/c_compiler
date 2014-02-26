__author__ = 'samyvilar'

from itertools import izip_longest, imap, takewhile, repeat, starmap, chain

from utils.sequences import peek, consume, peek_or_terminal
from utils.rules import rules, set_rules

from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.types import c_type, FunctionType, PointerType, IntegralType, StructType, safe_type_coercion
from front_end.parser.types import VAListType, member, UnionType
from front_end.parser.ast.expressions import ArraySubscriptingExpression, ArgumentExpressionList, FunctionCallExpression
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, CastExpression

from utils.errors import error_if_not_type, error_if_not_value


# Subscript operator can only be called on an expression that returns a pointer type.
def subscript_oper(tokens, symbol_table, primary_exp):
    location = error_if_not_type(c_type(primary_exp), PointerType) and loc(consume(tokens))
    expr = symbol_table['__ expression __'](tokens, symbol_table)     # subscript must be of Integral Type.
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET) and error_if_not_type(c_type(expr), IntegralType)
    return ArraySubscriptingExpression(primary_exp, expr, c_type(c_type(primary_exp))(location), location)


# list of 1 or more expressions to be used as arguments to a function call.
def argument_expression_list(tokens, symbol_table):  # : assignment_expression (',' assignment_expression)*
    assignment_expression = symbol_table['__ assignment_expression __']
    return chain(
        (assignment_expression(tokens, symbol_table),),
        starmap(
            assignment_expression,
            takewhile(lambda i: peek(i[0]) == TOKENS.COMMA and consume(i[0]), repeat((tokens, symbol_table)))
        )
    )


def arguments(func_type):
    return chain(
        takewhile(lambda arg: not isinstance(c_type(arg), VAListType), func_type),  # emit all non-variable arguments ...
        takewhile(lambda arg: isinstance(c_type(arg), VAListType), repeat(func_type[-1]))  # continuously emit last parameter
    )


def get_args(tokens, symbol_table, func_type):
    if peek_or_terminal(tokens) != TOKENS.RIGHT_PARENTHESIS:   # check the arguments.
        for arg_decl, arg in takewhile(
            lambda args: not (isinstance(c_type(args[0]), VAListType) and args[1] is None),
            izip_longest(arguments(func_type), argument_expression_list(tokens, symbol_table))
        ):
            if arg is None:
                raise ValueError('{l} Function call with not enough arguments specified.'.format(l=l))
            elif arg_decl is None:
                raise ValueError('{l} Function call with to many arguments specified'.format(l=loc(arg)))
            elif not safe_type_coercion(c_type(arg), c_type(arg_decl)):
                raise ValueError('{l} Function call, could not coerce argument from {f_type} to {t_type}'.format(
                    l=loc(arg), f_type=c_type(arg), t_type=c_type(arg_decl),
                ))
            yield CastExpression(arg, c_type(arg if isinstance(c_type(arg_decl), VAListType) else arg_decl), loc(arg))


# Function call can only be called on an expression that return a pointer to a function type or a function_type.
def function_call(tokens, symbol_table, primary_exp):
    l = loc(consume(tokens))
    func_type = error_if_not_type(c_type(c_type(primary_exp)), FunctionType)
    # get expression arguments.
    expression_argument_list = ArgumentExpressionList(tuple(get_args(tokens, symbol_table, func_type)), l)
    return error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS) and FunctionCallExpression(
        primary_exp, expression_argument_list, c_type(func_type)(l), l
    )


def dot_oper(tokens, symbol_table, primary_exp):
    l = (error_if_not_type(c_type(primary_exp), (StructType, UnionType)) or 1) and loc(consume(tokens))
    member_name = error_if_not_type(consume(tokens, ''), IDENTIFIER)
    return ElementSelectionExpression(primary_exp, member_name, c_type(member(c_type(primary_exp), member_name))(l), l)


def arrow_operator(tokens, symbol_table, primary_exp):
    l = loc(consume(tokens))
    _ = error_if_not_type(c_type(primary_exp), PointerType), \
        error_if_not_type(c_type(c_type(primary_exp)), (StructType, UnionType))
    member_name = error_if_not_type(consume(tokens, EOFLocation), IDENTIFIER)
    return ElementSelectionThroughPointerExpression(
        primary_exp, member_name, c_type(member(c_type(c_type(primary_exp)), member_name))(l), l
    )


def inc_dec(tokens, symbol_table, primary_exp):  # Postfix unary operators ++, --
    token = consume(tokens)
    return rules(inc_dec)[token](primary_exp, c_type(primary_exp)(loc(token)), loc(token))
set_rules(inc_dec, ((TOKENS.PLUS_PLUS, PostfixIncrementExpression), (TOKENS.MINUS_MINUS, PostfixDecrementExpression)))


def postfix_expression(tokens, symbol_table):
    """
    : primary_expression
    (       '[' expression ']'
            |   '(' ')'
            |   '(' argument_expression_list ')'
            |   '.' IDENTIFIER
            |   '->' IDENTIFIER
            |   '++'
            |   '--'        )*
    """
    type_name, expression, initializer, primary_expression = imap(
        symbol_table.__getitem__,
        ('__ type_name __', '__ expression __', '__ initializer __', '__ primary_expression __')
    )
    # if primary_exp is None:
    #     if peek_or_terminal(tokens) == TOKENS.LEFT_PARENTHESIS and consume(tokens):
    #         # Again slight ambiguity since primary_expression may start with '(' expression ')'
    #         # can't call cast_expression since it will try to call postfix_expression.
    #         if is_type_name(peek_or_terminal(tokens), symbol_table):
    #             ctype, _ = type_name(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    #             primary_exp = CompoundLiteral(initializer(tokens, symbol_table), ctype, loc(ctype))
    #         else:  # if we saw a parenthesis and it wasn't a type_name then it must be primary_expr `(` expression `)`
    #             primary_exp, _ = expression(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    #     else:
    #         primary_exp = primary_expression(tokens, symbol_table)
    primary_exp = primary_expression(tokens, symbol_table)
    while peek_or_terminal(tokens) in rules(postfix_expression):
        primary_exp = rules(postfix_expression)[peek(tokens)](tokens, symbol_table, primary_exp)

    return primary_exp
set_rules(
    postfix_expression,
    (
        (TOKENS.LEFT_BRACKET, subscript_oper),
        (TOKENS.LEFT_PARENTHESIS, function_call),
        (TOKENS.DOT, dot_oper),
        (TOKENS.ARROW, arrow_operator),
        (TOKENS.PLUS_PLUS, inc_dec),
        (TOKENS.MINUS_MINUS, inc_dec),
    )
)
