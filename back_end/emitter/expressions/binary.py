__author__ = 'samyvilar'

import sys
from itertools import chain, izip, repeat, imap, ifilterfalse
from utils.sequences import all_but_last
from utils.rules import set_rules, rules
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.ast.expressions import oper, left_exp, right_exp, AddressOfExpression, IdentifierExpression

from front_end.parser.types import unsigned, c_type, base_c_type, ArrayType
from front_end.parser.types import PointerType, FloatType, LongType, IntegerType, DoubleType, IntegralType, NumericType
from front_end.parser.types import double_type, integer_type, float_type, void_pointer_type, long_type

from back_end.emitter.expressions.cast import cast

from back_end.virtual_machine.instructions.architecture import Loads, logical_or, logical_and, get_operations_by_size
from back_end.virtual_machine.instructions.architecture import dup, swap, push, load, set_instr
from back_end.virtual_machine.instructions.architecture import load_most_significant_bit_flag, load_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_zero_flag, load_non_zero_flag
from back_end.virtual_machine.instructions.architecture import load_non_zero_non_most_significant_bit_flag
from back_end.virtual_machine.instructions.architecture import load_non_zero_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_zero_most_significant_bit_flag
from back_end.virtual_machine.instructions.architecture import load_zero_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_non_carry_borrow_flag
from back_end.virtual_machine.instructions.architecture import load_non_most_significant_bit_flag

import back_end.virtual_machine.instructions.architecture as architecture

from back_end.emitter.c_types import size_extended, size, size_arrays_as_pointers

current_module = sys.modules[__name__]


def binary(func):
    def wrapper(*args):
        args = func(*args)  # TODO: fix subtract so I can remove this conditional!
        if len(args) == 1 and isinstance(args, architecture.instruction):
            return args
        return getattr(sys.modules[__name__], func.__name__).rules[
            base_c_type(args[3][0])][size_arrays_as_pointers(args[3][0])](*args)

    wrapper.rules = {IntegralType: get_operations_by_size(func.__name__)}
    if hasattr(architecture, func.__name__ + '_float'):
        wrapper.rules[NumericType] = get_operations_by_size(func.__name__ + '_float', architecture.float_sizes)

    return wrapper


def calculate_pointer_offset(instrs, pointer_type, location):
    return multiply(
        instrs,
        push(size_extended(c_type(pointer_type)), location),
        location,
        (
            PointerType(c_type(pointer_type), location=location),
            pointer_type,
            LongType(LongType(location=location), location=location, unsigned=True)
        )
    )


def pointer_arithmetic(l_instrs, r_instrs, location, operand_types):
    exp_c_type, left_exp_c_type, right_exp_c_type = operand_types
    if isinstance(left_exp_c_type, PointerType) and isinstance(right_exp_c_type, IntegralType):
        r_instrs = calculate_pointer_offset(r_instrs, left_exp_c_type, location)  # right operand is index ...
    elif isinstance(left_exp_c_type, IntegralType) and isinstance(right_exp_c_type, PointerType):
        l_instrs = calculate_pointer_offset(l_instrs, right_exp_c_type, location)  # left operand is index ...

    return l_instrs, r_instrs, location, operand_types


def add(l_instrs, r_instrs, location, operand_types):
    if all(imap(isinstance, operand_types[1:], repeat(PointerType))):
        raise ValueError('{l} Cannot add two pointers!'.format(l=location))

    return pointer_arithmetic(l_instrs, r_instrs, location, operand_types)


def subtract(l_instrs, r_instrs, location, operand_types):
    exp_c_type, left_exp_c_type, right_exp_c_type = operand_types
    if all(imap(isinstance, operand_types[1:], repeat(PointerType))):  # subtracting two pointers ...
        return divide(
            subtract.rules[base_c_type(void_pointer_type)][size(void_pointer_type)](l_instrs, r_instrs, location),
            push(size_extended(c_type(c_type(left_exp_c_type))), location),
            location,
            operand_types
        )

    return pointer_arithmetic(l_instrs, r_instrs, location, operand_types)


binary_operation_names = 'add', 'subtract', 'multiply', 'divide', \
    'mod', 'shift_left', 'shift_right', 'bitwise_and', 'bitwise_or', 'bitwise_xor', \
    'compare'

for _name in ifilterfalse(
        lambda n, current_module=current_module: hasattr(current_module, n), binary_operation_names
):
    _f = lambda *args: args
    _f.__name__ = _name
    setattr(current_module, _name, _f)

for _name, _func in izip(binary_operation_names, imap(getattr, repeat(current_module), binary_operation_names)):
    setattr(current_module, _name, binary(_func))


def compare(l_instrs, r_instrs, location, operand_types, flags=()):
    operand = max(operand_types[1:])
    return compare_instr_kind_rules[base_c_type(operand)](size_arrays_as_pointers(operand))(
        l_instrs, r_instrs, location, flags
    )
compare_instr_kind_rules = {NumericType: architecture.get_compare_float, IntegralType: architecture.get_compare}


sign_sensitive_comparison_names = {'less_than', 'greater_than', 'less_than_or_equal', 'greater_than_or_equal'}
non_sign_sensitive_comparison_names = {'equal', 'not_equal'}
comparison_names = sign_sensitive_comparison_names | non_sign_sensitive_comparison_names


def _comparison(func):
    def func_wrapper(l_instrs, r_instrs, location, operand_types):
        flag_instr = (
            comparison_load_flags[func.__name__][unsigned(max(operand_types[1:]))]
            if func.__name__ in sign_sensitive_comparison_names else comparison_load_flags[func.__name__]
        )(location)

        # 2 instructions (Compare, Load*) ...
        return compare(*chain(func(l_instrs, r_instrs, location, operand_types), ((flag_instr,),)))
    return func_wrapper


for _name in comparison_names:
    f = lambda *args: args
    f.__name__ = _name
    setattr(current_module, _name, f)
    setattr(current_module, _name, _comparison(f))


comparison_load_flags = {
    'less_than': {
        True: load_carry_borrow_flag,  # For unsigned numbers.
        False: load_most_significant_bit_flag,  # For signed numbers.
    },
    'greater_than': {
        True: load_non_zero_carry_borrow_flag,  # For unsigned numbers
        False: load_non_zero_non_most_significant_bit_flag,  # For signed numbers.
    },
    'less_than_or_equal': {
        True: load_zero_carry_borrow_flag,
        False: load_zero_most_significant_bit_flag,
    },
    'greater_than_or_equal': {
        True: load_non_carry_borrow_flag,  # unsigned
        False: load_non_most_significant_bit_flag,  # signed
    },
    'equal': load_zero_flag,
    'not_equal': load_non_zero_flag
}


def relational_operators(expr, symbol_table):
    max_type = max(imap(c_type, (left_exp(expr), right_exp(expr))))
    expression = symbol_table['__ expression __']
    if isinstance(max_type, ArrayType):
        max_type = PointerType(c_type(max_type), loc(max_type))
    left_instrs = expression(left_exp(expr), symbol_table)
    right_instrs = expression(right_exp(expr), symbol_table)

    return rules(relational_operators)[oper(expr)](
        cast(left_instrs, c_type(left_exp(expr)), max_type, loc(expr)),
        cast(right_instrs, c_type(right_exp(expr)), max_type, loc(expr)),
        loc(expr),
        (c_type(expr), c_type(left_exp(expr)), c_type(right_exp(expr))),
    )
set_rules(
    relational_operators,
    (
        (TOKENS.EQUAL_EQUAL, equal),
        (TOKENS.NOT_EQUAL, not_equal),
        (TOKENS.LESS_THAN, less_than),
        (TOKENS.GREATER_THAN, greater_than),
        (TOKENS.LESS_THAN_OR_EQUAL, less_than_or_equal),
        (TOKENS.GREATER_THAN_OR_EQUAL, greater_than_or_equal)
    )
)



def logical_operators(expr, symbol_table):
    expression = symbol_table['__ expression __']
    return rules(logical_operators)[oper(expr)](
        expression(left_exp(expr), symbol_table), 
        expression(right_exp(expr), symbol_table),
        loc(expr),
        tuple(imap(size_arrays_as_pointers, imap(c_type, (expr, left_exp(expr), right_exp(expr)))))
    )
set_rules(logical_operators, ((TOKENS.LOGICAL_AND, logical_and), (TOKENS.LOGICAL_OR, logical_or)))


def arithmetic_and_bitwise_operators(expr, symbol_table):
    expression = symbol_table['__ expression __']
    left_instrs = expression(left_exp(expr), symbol_table)
    right_instrs = expression(right_exp(expr), symbol_table)

    to_type = c_type(expr)
    if isinstance(to_type, ArrayType):
        to_type = PointerType(c_type(to_type), loc(c_type(expr)))

    return rules(arithmetic_and_bitwise_operators)[oper(expr)](
        cast(left_instrs, c_type(left_exp(expr)), to_type, loc(expr)),
        cast(right_instrs, c_type(right_exp(expr)), to_type, loc(expr)),
        loc(expr),
        (to_type, c_type(left_exp(expr)), c_type(right_exp(expr))),
    )
set_rules(
    arithmetic_and_bitwise_operators,
    (
        (TOKENS.PLUS, add),
        (TOKENS.MINUS, subtract),
        (TOKENS.STAR, multiply),
        (TOKENS.FORWARD_SLASH, divide),
        (TOKENS.PERCENTAGE, mod),
        (TOKENS.SHIFT_LEFT, shift_left),
        (TOKENS.SHIFT_RIGHT, shift_right),
        (TOKENS.BAR, bitwise_or),
        (TOKENS.AMPERSAND, bitwise_and),
        (TOKENS.CARET, bitwise_xor),
    )
)


def assign(expr, symbol_table):
    expression = symbol_table['__ expression __']
    return set_instr(
        chain(
            cast(expression(right_exp(expr), symbol_table), c_type(right_exp(expr)), c_type(expr), loc(expr)),
            # remove default Load instruction, emit Set instruction ...
            all_but_last(expression(left_exp(expr), symbol_table), Loads, loc(expr)),
        ),
        size_arrays_as_pointers(c_type(expr)),  # get the size exp returns an array make sure its treated as pointer ...
        loc(expr),
    )


def patch_comp_assignment(instrs, expr_type, location):
    # At this point the stack contains the Address followed by the calculated value ...
    # we need to swap them and call set, but we mut be careful that both have the same size before calling swap
    # or we could corrupt the value ...
    if size(expr_type) == size(void_pointer_type):  # result type and pointer type (address) equal no alignment required
        return chain(instrs, set_instr(swap(size(void_pointer_type), location), size(void_pointer_type), location))

    if size(expr_type) < size(void_pointer_type):  # size of result type is less than address we need to align
        if isinstance(expr_type, DoubleType):  # since we are using cast to the alignment we need too interpret
            assert size(double_type) == size(long_type)   # result type as integral type for casting may change value
            expr_type = LongType(location, unsigned=True)
        elif isinstance(expr_type, FloatType):
            assert size(float_type) == size(integer_type)
            expr_type = IntegerType(location, unsigned=True)

        return cast(  # convert the value back to its original size removing any alignment added bytes after set ...
            set_instr(  # set values assuming little endian architecture  TODO: check on that assertion!
                chain(cast(instrs, expr_type, void_pointer_type, location), swap(size(void_pointer_type), location)),
                size(expr_type),  # if sizes differ, cast value to pointer type extending bytes, and swap
                location
            ),
            void_pointer_type,
            expr_type,
            location
        )
    else:
        raise ValueError('{l} unable to patch compound assignment value size {s} exceeds address size {a}'.format(
            l=location, s=size(expr_type), a=size(void_pointer_type)
        ))


# not much of an improvement ....
def simple_numeric_assignment_no_casting(expr, symbol_table, operation):
    expression = symbol_table['__ expression __']
    # used when the left operand is an identifier so we can re-emit binaries instead of using expensive Dup instr
    return set_instr(
        chain(
            operation(
                expression(left_exp(expr), symbol_table),
                expression(right_exp(expr), symbol_table),
                loc(expr),
                tuple(imap(c_type, (expr, left_exp(expr), right_exp(expr))))
            ),
            expression(
                AddressOfExpression(left_exp(expr), PointerType(c_type(right_exp(expr)), loc(expr)), loc(expr)),
                symbol_table,
            )
        ),
        size(c_type(expr)),
        loc(expr),
    )


def patch_comp_left_instrs(instrs, location, value_size):
    return load(                                     # duplicate address ...
        chain(all_but_last(instrs, Loads, location), dup(size(void_pointer_type), location)),
        value_size,
        location
    )


def compound_assignment(expr, symbol_table):
    assert all(imap(isinstance, imap(c_type, (left_exp(expr), right_exp(expr))), repeat(NumericType)))
    assert not isinstance(c_type(left_exp(expr)), ArrayType)

    if isinstance(left_exp(expr), IdentifierExpression) and \
       base_c_type(c_type(left_exp(expr))) == base_c_type(c_type(right_exp(expr))) and \
       size(c_type(left_exp(expr))) == size(c_type(right_exp(expr))):
        # check that both operands are of the same kind (integral vs numeric) and have the same size ...
        return simple_numeric_assignment_no_casting(expr, symbol_table, rules(compound_assignment)[oper(expr)])

    max_type = max(imap(c_type, (left_exp(expr), right_exp(expr))))  # cast to largest type.
    expression = symbol_table['__ expression __']
    left_instrs = cast(  # cast to max_type
        patch_comp_left_instrs(expression(left_exp(expr), symbol_table),  loc(expr), size(c_type(left_exp(expr)))),
        c_type(left_exp(expr)),
        max_type,
        loc(expr),
    )
    right_instrs = cast(expression(right_exp(expr), symbol_table), c_type(right_exp(expr)), max_type, loc(expr))
    return patch_comp_assignment(
        cast(  # Cast the result back, swap the value and the destination address call set to save.
            rules(compound_assignment)[oper(expr)](
                left_instrs,
                right_instrs,
                loc(expr),
                (max_type, c_type(left_exp(expr)), c_type(right_exp(expr)))
            ),
            max_type,
            c_type(expr),
            loc(expr)
        ),
        c_type(expr),
        loc(expr),
    )
set_rules(
    compound_assignment,
    (
        (TOKENS.PLUS_EQUAL,          add),
        (TOKENS.MINUS_EQUAL,         subtract),
        (TOKENS.STAR_EQUAL,          multiply),
        (TOKENS.FORWARD_SLASH_EQUAL, divide),

        (TOKENS.SHIFT_LEFT_EQUAL,    shift_left),
        (TOKENS.SHIFT_RIGHT_EQUAL,   shift_right),
        (TOKENS.PERCENTAGE_EQUAL,    mod),

        (TOKENS.AMPERSAND_EQUAL,     bitwise_and),
        (TOKENS.CARET_EQUAL,         bitwise_xor),
        (TOKENS.BAR_EQUAL,           bitwise_or)
    )
)


def binary_expression(expr, symbol_table):
    return rules(binary_expression)[oper(expr)](expr, symbol_table)
binary_operators = arithmetic_and_bitwise_operators, relational_operators, compound_assignment, logical_operators
set_rules(
    binary_expression,
    chain(
        ((TOKENS.EQUAL, assign),),
        chain.from_iterable(imap(izip, imap(rules, binary_operators), imap(repeat, binary_operators)))
    )
)
