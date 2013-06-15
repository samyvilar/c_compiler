__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.ast.expressions import oper, left_exp, right_exp

from front_end.parser.types import IntegralType, NumericType, c_type, base_c_type, unsigned

from back_end.emitter.expressions.cast import cast
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod, ShiftLeft
from back_end.virtual_machine.instructions.architecture import Or, Xor, And, Load, Set, Swap, Pop, ShiftRight
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat
from back_end.virtual_machine.instructions.architecture import LoadZeroFlag, LoadOverflowFlag, LoadCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import Push, Integer, Dup, Pass, JumpFalse, JumpTrue, Address

from back_end.emitter.types import size


def add_pointers():  # TODO: implement pointer math.
    pass


def add(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [add.rules[base_c_type(operand_types)](location)]
add.rules = {
    IntegralType: Add,
    NumericType: AddFloat,
}


def subtract_pointers():
    pass


def subtract(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [subtract.rules[base_c_type(operand_types)](location)]
subtract.rules = {
    IntegralType: Subtract,
    NumericType: SubtractFloat
}


def multiply(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [multiply.rules[base_c_type(operand_types)](location)]
multiply.rules = {
    IntegralType: Multiply,
    NumericType: MultiplyFloat
}


def divide(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [divide.rules[base_c_type(operand_types)](location)]
divide.rules = {
    IntegralType: Divide,
    NumericType: DivideFloat,
}


def mod(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [Mod(location)]


def shift_left(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [ShiftLeft(location)]


def shift_right(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [ShiftRight(location)]


def bit_and(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [And(location)]


def bit_or(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [Or(location)]


def bit_xor(l_instrs, r_instrs, location, operand_types):
    return l_instrs + r_instrs + [Xor(location)]


def compare_numbers(l_instrs, r_instrs, location, operand_types):
    return subtract(l_instrs, r_instrs, location, operand_types) + [Pop(location)]
compare_numbers.rules = {
    True: LoadCarryBorrowFlag,  # For unsigned numbers.
    False: LoadOverflowFlag,  # For signed numbers.
}


# One number is said to be less than another when their difference is negative (Either carry/Overflow)
def less_than(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(l_instrs, r_instrs, location, operand_types) + [
        compare_numbers.rules[unsigned(operand_types)](location)
    ]


# One number is said to be greater than another when their difference is positive.
def greater_than(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(l_instrs, r_instrs, location, operand_types) + [
        LoadZeroFlag(location),
        Push(location, Integer(1, location)),
        Xor(location),  # check the numbers are not equal
        compare_numbers.rules[unsigned(operand_types)](location),
        Push(location, Integer(1, location)),  # and not less than another
        Xor(location),
        And(location),
    ]


# Two number are said to be equal if their difference is zero.
def less_than_or_equal(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(l_instrs, r_instrs, location, operand_types) + [
        LoadZeroFlag(location),
        compare_numbers.rules[unsigned(operand_types)](location),
        Or(location),
    ]


def greater_than_or_equal(l_instrs, r_instrs, location, operand_types):
    return less_than(l_instrs, r_instrs, location, operand_types) + [
        Push(location, Integer(1, location)),
        Xor(location),  # Invert carry/overflow flag.
    ]


def equal(l_instrs, r_instrs, location, operand_types):
    return compare_numbers(l_instrs, r_instrs, location, operand_types) + [LoadZeroFlag(location)]


def not_equal(l_instrs, r_instrs, location, operand_types):
    return equal(l_instrs, r_instrs, location, operand_types) + [Push(location, Integer(1, location)), Xor(location)]


def short_circuit_logical(l_instrs, r_instrs, jump_type, location, operand_types):
    end_instr = Pass(location)
    return l_instrs + [Dup(location), jump_type(location, Address(end_instr, location)), Pop(location)] + r_instrs + [
        end_instr
    ]


def logical_and(l_instrs, r_instrs, location, operand_types):
    return short_circuit_logical(l_instrs, r_instrs, JumpFalse, location, operand_types)


def logical_or(l_instrs, r_instrs, location, operand_types):
    return short_circuit_logical(l_instrs, r_instrs, JumpTrue, location, operand_types)


def logical_bin_expression(expr, symbol_table, stack, expression_func, jump_props):
    max_type = max(c_type(left_exp(expr)), c_type(right_exp(expr)))
    left_instrs = expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props)
    right_instrs = expression_func(right_exp(expr), symbol_table, stack, expression_func, jump_props)

    return logical_bin_expression.rules[oper(expr)](
        cast(left_instrs, c_type(left_exp(expr)), max_type, loc(expr)),
        cast(right_instrs, c_type(right_exp(expr)), max_type, loc(expr)),
        loc(expr),
        max_type,
    )

logical_bin_expression.rules = {
    TOKENS.LESS_THAN: less_than,
    TOKENS.GREATER_THAN: greater_than,
    TOKENS.LESS_THAN_OR_EQUAL: less_than_or_equal,
    TOKENS.GREATER_THAN_OR_EQUAL: greater_than_or_equal,
    TOKENS.EQUAL_EQUAL: equal,
    TOKENS.NOT_EQUAL: not_equal,

    TOKENS.LOGICAL_AND: logical_and,
    TOKENS.LOGICAL_OR: logical_or,
}


def bin_expression(expr, symbol_table, stack, expression_func, jump_props):
    left_instrs = expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props)
    right_instrs = expression_func(right_exp(expr), symbol_table, stack, expression_func, jump_props)

    return bin_expression.rules[oper(expr)](
        cast(left_instrs, c_type(left_exp(expr)), c_type(expr), loc(expr)),
        cast(right_instrs, c_type(right_exp(expr)), c_type(expr), loc(expr)),
        loc(expr),
        c_type(expr),
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


def set_instr(instrs, location, set_size):
    assert isinstance(instrs[-1], Load)
    instrs[-1] = Set(location, Integer(set_size, location))
    return instrs


def assign(expr, symbol_table, stack, expression_func, jump_props):
    right_instrs = expression_func(right_exp(expr), symbol_table, stack, expression_func, jump_props)
    left_instrs = expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props)
    return set_instr(right_instrs + left_instrs, loc(expr), size(c_type(expr)))


def patch_comp_left_instrs(instrs, location):
    load_instr = instrs.pop()
    assert isinstance(load_instr, Load)
    instrs.append(Dup(location))  # Duplicate the load address of the value being assigned to.
    instrs.append(load_instr)
    return instrs


def patch_comp_assignment(instrs, set_size):
    return instrs + [Swap(loc(operator)), Set(loc(operator), set_size)]


def comp_integral_assign(expr, symbol_table, stack, expression_func, jump_props):
    assert isinstance(c_type(left_exp(expr)), IntegralType) and isinstance(c_type(right_exp(expr)), IntegralType)

    left_instrs = patch_comp_left_instrs(
        expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props), loc(expr)
    )
    right_instrs = expression_func(right_exp(expr), symbol_table, stack, expression_func, jump_props)
    return patch_comp_assignment(
        comp_integral_assign.rules[oper(expr)](left_instrs, right_instrs, loc(operator), c_type(expr)),
        size(c_type(expr))
    )
comp_integral_assign.rules = {
    TOKENS.SHIFT_LEFT_EQUAL: shift_left,
    TOKENS.SHIFT_RIGHT_EQUAL: shift_right,
    TOKENS.AMPERSAND_EQUAL: bit_and,
    TOKENS.CARET_EQUAL: bit_xor,
    TOKENS.BAR_EQUAL: bit_or,
    TOKENS.PERCENTAGE_EQUAL: mod,
}


def comp_numeric_assign(expr, symbol_table, stack, expression_func, jump_props):
    max_type = max(c_type(left_exp(expr)), c_type(right_exp(expr)))  # cast to largest type.

    left_instrs = cast(
        patch_comp_left_instrs(
            expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props),  loc(expr)
        ),
        c_type(left_exp(expr)),
        max_type,
        loc(expr),
    )
    right_instrs = cast(
        expression_func(right_exp(expr), symbol_table, stack, expression_func, jump_props),
        c_type(right_exp(expr)),
        max_type,
        loc(expr)
    )
    return patch_comp_assignment(
        cast(  # Cast the result back, swap the value and the destination address call set to save.
            comp_numeric_assign.rules[oper(expr)](left_instrs, right_instrs, loc(expr), max_type),
            max_type,
            c_type(expr),
            loc(expr)
        ),
        size(c_type(expr))
    )
comp_numeric_assign.rules = {
    TOKENS.PLUS_EQUAL: add,
    TOKENS.MINUS_EQUAL: subtract,
    TOKENS.STAR_EQUAL: multiply,
    TOKENS.FORWARD_SLASH_EQUAL: divide,
}


def compound_assignment(expr, symbol_table, stack, expression_func, jump_props):
    return compound_assignment.rules[operator](expr, symbol_table, stack, expression_func, jump_props)
compound_assignment.rules = {rule for rule in comp_integral_assign.rules}
compound_assignment.rules.update(rule for rule in comp_numeric_assign.rules)


def binary_expression(expr, symbol_table, stack, expression_func, jump_props):
    return binary_expression.rules[oper(expr)](expr, symbol_table, stack, expression_func, jump_props)
binary_expression.rules = {TOKENS.EQUAL: assign}
binary_expression.rules.update({operator: bin_expression for operator in bin_expression.rules})
binary_expression.rules.update({operator: compound_assignment for operator in compound_assignment.rules})
binary_expression.rules.update({operator: logical_bin_expression for operator in logical_bin_expression.rules})