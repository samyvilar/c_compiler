__author__ = 'samyvilar'

from itertools import chain
from front_end.loader.locations import loc

from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.types import c_type, ArrayType

from back_end.virtual_machine.instructions.architecture import Push, Allocate, PushFrame, PopFrame, Address, Load, Set
from back_end.virtual_machine.instructions.architecture import Integer, Multiply, Add, LoadStackPointer, Enqueue
from back_end.virtual_machine.instructions.architecture import AbsoluteJump, LoadBaseStackPointer
from back_end.emitter.c_types import size, struct_member_offset


# A pure implemented of Postfix Expressions are quite hard if not impossible on completely stack based machines, since
# we can't allocate anything on the stack in the middle of an expression, so the value (memory) will be copied to an
# aux memory location
def inc_dec(expr, symbol_table, expression_func):
    instrs = expression_func(exp(expr), symbol_table, expression_func)
    temp = next(instrs)
    for instr in instrs:
        yield temp
        temp = instr
    if isinstance(temp, Load):
        yield Enqueue(loc(expr), size(Address()))  # enqueue two copies one for loading and the other for setting.
        yield Enqueue(loc(expr), size(Address()))
        yield temp
    else:
        raise ValueError('Expected load instr')


def function_call(expr, symbol_table, expression_func):
    return_instr = PopFrame(loc(expr))  # once the function returns remove created frame
    return chain(
        chain(
            (Allocate(loc(expr), size(c_type(expr))),),
            expression_func(left_exp(expr), symbol_table, expression_func),  # we must load addr before gen new frame
            (
                PushFrame(loc(expr)),
                Push(loc(expr), Address(return_instr, loc(expr))),
            ),
            *(expression_func(arg, symbol_table, expression_func) for arg in right_exp(expr))
        ),
        (
            LoadBaseStackPointer(loc(expr)),
            Push(loc(expr), size(Address())),
            Add(loc(expr)),
            Load(loc(expr), size(Address())),
            AbsoluteJump(loc(expr)),
            return_instr,
            Allocate(loc(expr), -1 * size(Address())),  # de-allocate function address.
        ),
    )


def array_subscript(expr, symbol_table, expression_func):
    return chain(
        expression_func(left_exp(expr), symbol_table, expression_func),
        expression_func(right_exp(expr), symbol_table, expression_func),
        (
            # Calculate Offset.
            Push(loc(expr), size(c_type(right_exp(expr)))),
            Multiply(loc(expr)),
            Add(loc(expr)),
        ),
        () if isinstance(c_type(expr), ArrayType) else (Load(loc(expr), size(c_type(right_exp(expr)))),)
    )


def element_instrs(struct_obj, member_name, location):
    yield Push(location, Integer(struct_member_offset(struct_obj, member_name), location))
    yield Add(location)
    if not isinstance(c_type(struct_obj.members[member_name]), ArrayType):
        yield Load(location, size(c_type(struct_obj.members[member_name])))


# Element selection is a bit tricky, the whole struct will be loaded onto the stack, we need to deallocate it
# and only copy/select the specific value.
def element_selection(expr, symbol_table, expression_func):
    instrs = expression_func(left_exp(expr), symbol_table, expression_func)
    value = next(instrs)
    for instr in instrs:
        yield value
        value = instr
    if isinstance(value, Load):
        for i in element_instrs(c_type(left_exp(expr)), right_exp(expr), loc(expr)):
            yield i
    else:
        yield value
        struct_size = size(c_type(left_exp(expr)))
        member_size = size(Address) if isinstance(c_type(expr), ArrayType) else size(c_type(expr))
        yield LoadStackPointer(loc(expr))
        yield Push(loc(expr), Integer(struct_size, loc(expr)))
        yield Add(loc(expr))  # calculate starting address of structure
        yield Push(loc(expr), Integer(struct_member_offset(c_type(left_exp(expr)), right_exp(expr)), loc(expr)))
        yield Add(loc(expr))  # calculate member offset address.
        if not isinstance(c_type(expr), ArrayType):
            yield Load(loc(expr), member_size)
        yield LoadStackPointer(loc(expr))
        yield Push(loc(expr), Integer(struct_size + member_size, loc(expr)))
        yield Add(loc(expr))
        yield Set(loc(expr), size(c_type(expr)))
        yield Allocate(loc(expr), -1 * (struct_size - member_size))


def element_section_pointer(expr, symbol_table, expression_func):
    return chain(
        expression_func(left_exp(expr), symbol_table, expression_func),
        element_instrs(c_type(c_type(left_exp(expr))), right_exp(expr), loc(expr))
    )


def postfix_expression(expr, symbol_table, expression_func):
    return postfix_expression.rules[type(expr)](expr, symbol_table, expression_func)
postfix_expression.rules = {
    PostfixIncrementExpression: inc_dec,
    PostfixDecrementExpression: inc_dec,
    FunctionCallExpression: function_call,
    ArraySubscriptingExpression: array_subscript,
    ElementSelectionExpression: element_selection,
    ElementSelectionThroughPointerExpression: element_section_pointer
}
