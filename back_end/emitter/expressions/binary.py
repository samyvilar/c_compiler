__author__ = 'samyvilar'

from itertools import chain, izip, repeat
from utils.sequences import all_but_last
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.ast.expressions import oper, left_exp, right_exp, AddressOfExpression, IdentifierExpression

from front_end.parser.types import IntegralType, NumericType, c_type, base_c_type, unsigned, void_pointer_type
from front_end.parser.types import PointerType

from back_end.emitter.expressions.cast import cast
from back_end.virtual_machine.instructions.architecture import Load
from back_end.virtual_machine.instructions.architecture import add as add_instr, subtract as subtract_instr
from back_end.virtual_machine.instructions.architecture import multiply as multiply_instr, divide as divide_instr
from back_end.virtual_machine.instructions.architecture import mod as mod_instr, shift_left as shift_left_instr
from back_end.virtual_machine.instructions.architecture import shift_right as shift_right_instr
from back_end.virtual_machine.instructions.architecture import or_bitwise as or_bitwise_instr
from back_end.virtual_machine.instructions.architecture import and_bitwise as and_bitwise_instr
from back_end.virtual_machine.instructions.architecture import xor_bitwise as xor_bitwise_instr, load_instr, set_instr
from back_end.virtual_machine.instructions.architecture import add_float as add_float_instr
from back_end.virtual_machine.instructions.architecture import subtract_float as subtract_float_instr
from back_end.virtual_machine.instructions.architecture import multiply_float as multiply_float_instr
from back_end.virtual_machine.instructions.architecture import divide_float as divide_float_instr
from back_end.virtual_machine.instructions.architecture import load_zero_flag, logical_or, logical_and
from back_end.virtual_machine.instructions.architecture import load_most_significant_bit_flag, load_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_non_zero_flag

from back_end.virtual_machine.instructions.architecture import push
from back_end.virtual_machine.instructions.architecture import dup, swap, compare, compare_floats
from back_end.virtual_machine.instructions.architecture import load_non_zero_non_most_significant_bit_flag
from back_end.virtual_machine.instructions.architecture import load_non_zero_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_zero_most_significant_bit_flag
from back_end.virtual_machine.instructions.architecture import load_zero_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_non_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_non_most_significant_bit_flag


from back_end.emitter.c_types import size_extended, size


def calculate_pointer_offset(instrs, pointer_type, location):
    return multiply_instr(instrs, push(size_extended(c_type(pointer_type)), location), location)


def add(l_instrs, r_instrs, location, operand_types):
    if isinstance(operand_types[1], PointerType) and isinstance(operand_types[2], PointerType):
        raise ValueError('{l} Cannot add two pointers!'.format(l=location))
    elif isinstance(operand_types[1], PointerType) and isinstance(operand_types[2], IntegralType):
        # right operand is index ...
        r_instrs = calculate_pointer_offset(r_instrs, operand_types[1], location)
    elif isinstance(c_type(operand_types[2]), PointerType) and isinstance(c_type(operand_types[1]), IntegralType):
        # left operand is index ...
        l_instrs = calculate_pointer_offset(l_instrs, operand_types[2], location)

    return add.rules[base_c_type(operand_types[0])](l_instrs, r_instrs, location)
add.rules = {
    IntegralType: add_instr,
    NumericType: add_float_instr,
}


def subtract(l_instrs, r_instrs, location, operand_types):
    if isinstance(operand_types[1], PointerType) and isinstance(operand_types[2], PointerType):
        return divide_instr(
            subtract.rules[base_c_type(operand_types[0])](l_instrs, r_instrs, location),
            push(size_extended(c_type(operand_types[1])), location),
            location,
        )
    if isinstance(operand_types[1], PointerType) and isinstance(operand_types[2], IntegralType):
        # right_instr is index ...
        r_instrs = calculate_pointer_offset(r_instrs, operand_types[1], location)
    elif isinstance(operand_types[2], PointerType) and isinstance(operand_types[1], IntegralType):
        # left_instr is index
        l_instrs = calculate_pointer_offset(l_instrs, operand_types[2], location)

    return subtract.rules[base_c_type(operand_types[0])](l_instrs, r_instrs, location)
subtract.rules = {
    IntegralType: subtract_instr,
    NumericType: subtract_float_instr
}


def multiply(l_instrs, r_instrs, location, operand_types):
    return multiply.rules[base_c_type(operand_types[0])](l_instrs, r_instrs, location)
multiply.rules = {
    IntegralType: multiply_instr,
    NumericType: multiply_float_instr
}


def divide(l_instrs, r_instrs, location, operand_types):
    return divide.rules[base_c_type(operand_types[0])](l_instrs, r_instrs, location)
divide.rules = {
    IntegralType: divide_instr,
    NumericType: divide_float_instr,
}


def mod(l_instrs, r_instrs, location, _=None):
    return mod_instr(l_instrs, r_instrs, location)


def shift_left(l_instrs, r_instrs, location, _=None):
    return shift_left_instr(l_instrs, r_instrs, location)


def shift_right(l_instrs, r_instrs, location, _=None):
    return shift_right_instr(l_instrs, r_instrs, location)


def bit_and(l_instrs, r_instrs, location, _=None):
    return and_bitwise_instr(l_instrs, r_instrs, location)


def bit_or(l_instrs, r_instrs, location, _=None):
    return or_bitwise_instr(l_instrs, r_instrs,  location)


def bit_xor(l_instrs, r_instrs, location, _=None):
    return xor_bitwise_instr(l_instrs, r_instrs, location)


def compare_numbers(l_instrs, r_instrs, location, operand_types, flags=()):
    if isinstance(max(operand_types[1:]), IntegralType):
        return compare(l_instrs, r_instrs, location, flags)
    return compare_floats(l_instrs, r_instrs, location, flags)
compare_numbers.rules = {
    True: load_carry_borrow_flag,  # For unsigned numbers.
    False: load_most_significant_bit_flag,  # For signed numbers.
}


# One number is said to be less than another when their difference is negative (Either carry/msb)
def less_than(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(  # 2 instructions (Compare, Load*) ...
        l_instrs,
        r_instrs,
        location,
        operand_types,
        (compare_numbers.rules[unsigned(max(operand_types[1:]))](location),)
    )


# One number is said to be greater than another when their difference is non-zero and positive.
def greater_than(l_instrs, r_instrs, location, operand_types):
    return compare(  # 2 instructions (Compare, Load*) ...
        l_instrs,
        r_instrs,
        location,
        (greater_than.rules[unsigned(max(operand_types[1:]))](location),)
    )
greater_than.rules = {
    True: load_non_zero_carry_borrow_flag,  # For unsigned numbers
    False: load_non_zero_non_most_significant_bit_flag,  # For signed numbers.
}


def less_than_or_equal(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(  # 2 instructions ...
        l_instrs,
        r_instrs,
        location,
        operand_types,
        (less_than_or_equal.rules[unsigned(max(operand_types[1:]))](location),)
    )
less_than_or_equal.rules = {
    True: load_zero_carry_borrow_flag,
    False: load_zero_most_significant_bit_flag,
}


def greater_than_or_equal(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(  # 2 instructions ..
        l_instrs,
        r_instrs,
        location,
        operand_types,
        (greater_than_or_equal.rules[unsigned(max(operand_types[1:]))](location),)
    )
greater_than_or_equal.rules = {
    True: load_non_carry_borrow_flag,  # unsigned
    False: load_non_most_significant_bit_flag,  # signed
}


# Two number are said to be equal if their difference is zero.
def equal(l_instrs, r_instrs, location, operand_types):  # 2 instructions (COMPARE, LoadZero)
    return compare_numbers(l_instrs, r_instrs, location, operand_types, (load_zero_flag(location),))


def not_equal(l_instrs, r_instrs, location, operand_types):  # 2 instructions (COMPARE, LoadNonZero)
    return compare_numbers(l_instrs, r_instrs, location, operand_types, (load_non_zero_flag(location),))


def logical_operators(expr, symbol_table, expression_func):
    return logical_operators.rules[oper(expr)](
        expression_func(left_exp(expr), symbol_table, expression_func),
        expression_func(right_exp(expr), symbol_table, expression_func),
        loc(expr),
        (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr)))
    )
logical_operators.rules = {
    TOKENS.LOGICAL_AND: logical_and,
    TOKENS.LOGICAL_OR: logical_or,
}


def relational_operators(expr, symbol_table, expression_func):
    max_type = max(c_type(left_exp(expr)), c_type(right_exp(expr)))
    left_instrs = expression_func(left_exp(expr), symbol_table, expression_func)
    right_instrs = expression_func(right_exp(expr), symbol_table, expression_func)

    return relational_operators.rules[oper(expr)](
        cast(left_instrs, c_type(left_exp(expr)), max_type, loc(expr)),
        cast(right_instrs, c_type(right_exp(expr)), max_type, loc(expr)),
        loc(expr),
        (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr))),
    )
relational_operators.rules = {
    TOKENS.LESS_THAN: less_than,
    TOKENS.GREATER_THAN: greater_than,
    TOKENS.LESS_THAN_OR_EQUAL: less_than_or_equal,
    TOKENS.GREATER_THAN_OR_EQUAL: greater_than_or_equal,
    TOKENS.EQUAL_EQUAL: equal,
    TOKENS.NOT_EQUAL: not_equal,
}


def bin_expression(expr, symbol_table, expression_func):
    left_instrs = expression_func(left_exp(expr), symbol_table, expression_func)
    right_instrs = expression_func(right_exp(expr), symbol_table, expression_func)

    return bin_expression.rules[oper(expr)](
        cast(left_instrs, c_type(left_exp(expr)), c_type(expr), loc(expr)),
        cast(right_instrs, c_type(right_exp(expr)), c_type(expr), loc(expr)),
        loc(expr),
        (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr))),
    )
bin_expression.rules = {
    TOKENS.PLUS: add,
    TOKENS.MINUS: subtract,
    TOKENS.STAR: multiply,
    TOKENS.FORWARD_SLASH: divide,
    TOKENS.PERCENTAGE: mod,
    TOKENS.SHIFT_LEFT: shift_left,
    TOKENS.SHIFT_RIGHT: shift_right,
    TOKENS.BAR: bit_or,
    TOKENS.AMPERSAND: bit_and,
    TOKENS.CARET: bit_xor,
}


def assign(expr, symbol_table, expression_func):
    return set_instr(
        cast(
            expression_func(right_exp(expr), symbol_table, expression_func),
            c_type(right_exp(expr)),
            c_type(expr),
            loc(expr)
        ),
        size(c_type(expr)),
        loc(expr),
        addr_instrs=all_but_last(expression_func(left_exp(expr), symbol_table, expression_func), Load, loc(expr))
    )


def patch_comp_left_instrs(instrs, location):
    return load_instr(
        # duplicate address ...
        chain(all_but_last(instrs, Load, location), dup(size(void_pointer_type), location)),
        size(void_pointer_type),
        location
    )


def patch_comp_assignment(instrs, expr_type, location):
    # At this point the stack contains the Address followed by the value ...
    # we need to swap them and call set, but we mut be careful that both have the same size before calling swap
    # or we could corrupt the value ...
    assert size(expr_type) == size(void_pointer_type)
    return chain(
        instrs,
        set_instr(
            swap(size(void_pointer_type), location),
            size(void_pointer_type),
            location
        )
    )


# not much of an improvement ....
def simple_numeric_assignment_no_casting(expr, symbol_table, expression_func, operation):
    # used when the left operand is an identifier so we can re-emit binaries instead of using expensive Dup instr
    return set_instr(
        operation(
            expression_func(left_exp(expr), symbol_table, expression_func),
            expression_func(right_exp(expr), symbol_table, expression_func),
            loc(expr),
            (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr)))
        ),
        size(c_type(expr)),
        loc(expr),
        expression_func(
            AddressOfExpression(left_exp(expr), PointerType(c_type(right_exp(expr)), loc(expr)), loc(expr)),
            symbol_table,
            expression_func
        )
    )


def comp_integral_assign(expr, symbol_table, expression_func):
    assert isinstance(c_type(left_exp(expr)), IntegralType) and isinstance(c_type(right_exp(expr)), IntegralType)

    if isinstance(left_exp(expr), IdentifierExpression):
        return simple_numeric_assignment_no_casting(
            expr, symbol_table, expression_func, comp_integral_assign.rules[oper(expr)]
        )

    left_instrs = patch_comp_left_instrs(
        expression_func(left_exp(expr), symbol_table, expression_func), loc(expr)
    )

    right_instrs = expression_func(right_exp(expr), symbol_table, expression_func)
    return patch_comp_assignment(
        comp_integral_assign.rules[oper(expr)](left_instrs, right_instrs, loc(expr), c_type(expr)),

        (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr))),
        loc(expr),
    )
comp_integral_assign.rules = {
    TOKENS.SHIFT_LEFT_EQUAL: shift_left,
    TOKENS.SHIFT_RIGHT_EQUAL: shift_right,
    TOKENS.PERCENTAGE_EQUAL: mod,

    TOKENS.AMPERSAND_EQUAL: bit_and,
    TOKENS.CARET_EQUAL: bit_xor,
    TOKENS.BAR_EQUAL: bit_or,

}


def comp_numeric_assign(expr, symbol_table, expression_func):
    assert isinstance(c_type(left_exp(expr)), NumericType) and isinstance(c_type(right_exp(expr)), NumericType)

    if isinstance(left_exp(expr), IdentifierExpression) and \
            base_c_type(c_type(left_exp(expr))) == base_c_type(c_type(right_exp(expr))):
        return simple_numeric_assignment_no_casting(
            expr, symbol_table, expression_func, comp_numeric_assign.rules[oper(expr)]
        )

    max_type = max(c_type(left_exp(expr)), c_type(right_exp(expr)))  # cast to largest type.

    left_instrs = cast(
        patch_comp_left_instrs(expression_func(left_exp(expr), symbol_table, expression_func),  loc(expr)),
        c_type(left_exp(expr)),
        max_type,
        loc(expr),
    )
    right_instrs = cast(
        expression_func(right_exp(expr), symbol_table, expression_func),
        c_type(right_exp(expr)),
        max_type,
        loc(expr)
    )
    return patch_comp_assignment(
        cast(  # Cast the result back, swap the value and the destination address call set to save.
            comp_numeric_assign.rules[oper(expr)](
                left_instrs,
                right_instrs,
                loc(expr),
                (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr)))
            ),
            max_type,
            c_type(expr),
            loc(expr)
        ),
        max_type,
        loc(expr),
    )
comp_numeric_assign.rules = {
    TOKENS.PLUS_EQUAL: add,
    TOKENS.MINUS_EQUAL: subtract,
    TOKENS.STAR_EQUAL: multiply,
    TOKENS.FORWARD_SLASH_EQUAL: divide,
}


def compound_assignment(expr, symbol_table, expression_func):
    return compound_assignment.rules[oper(expr)](expr, symbol_table, expression_func)
compound_assignment.rules = dict(chain(
    izip(comp_integral_assign.rules, repeat(comp_integral_assign)),
    izip(comp_numeric_assign.rules, repeat(comp_numeric_assign)),
))


def binary_expression(expr, symbol_table, expression_func):
    return binary_expression.rules[oper(expr)](expr, symbol_table, expression_func)
binary_expression.rules = {TOKENS.EQUAL: assign}
binary_expression.rules.update(chain(
    izip(bin_expression.rules, repeat(bin_expression)),
    izip(compound_assignment.rules, repeat(compound_assignment)),
    izip(relational_operators.rules, repeat(relational_operators)),
    izip(logical_operators.rules, repeat(logical_operators)),
))