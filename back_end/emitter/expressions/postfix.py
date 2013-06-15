__author__ = 'samyvilar'

from front_end.loader.locations import loc

from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.types import c_type, ArrayType

from back_end.virtual_machine.instructions.architecture import Push, Allocate, PushFrame, PopFrame, Address, Load, Dup
from back_end.virtual_machine.instructions.architecture import Integer, Multiply, Add, LoadStackPointer, Enqueue, Dequeue
from back_end.virtual_machine.instructions.architecture import Swap, Set, AbsoluteJump
from back_end.emitter.instructions.data import load_instructions
from back_end.emitter.types import size, struct_member_offset


# A pure implemented of Postfix Expressions are quite hard if not impossible on completely stack based machines, since
# we can't allocate anything on the stack in the middle of an expression, so the value (memory) will be copied to an
# aux memory location
def inc_dec(value, expr, symbol_table, stack, expression_func, jump_props):
    instrs = expression_func(exp(expr), symbol_table, stack, expression_func, jump_props)
    load_instr = instrs.pop()
    assert isinstance(load_instr, Load)
    instrs.extend((Enqueue(loc(expr), size(c_type(expr))), load_instr))  # Save address for late instrs

    postfix_expression.late_instrs.extend((
        Dequeue(loc(expr), size(c_type(expr))),
        Dup(loc(expr)),
        Load(loc(expr), size(c_type(expr))),
        Push(loc(expr), Integer(value, loc(expr))),
        Add(loc(expr)),
        Swap(loc(expr)),
        Set(loc(expr), size(c_type(expr))),
        Allocate(loc(expr), Integer(-1 * size(c_type(expr)), loc(expr))),
    ))

    return instrs


def function_call(expr, symbol_table, stack, expression_func, jump_props):
    return_instr = PopFrame(loc(expr))  # once the function returns remove created frame
    instrs = [
        Allocate(loc(expr), size(c_type(expr))),  # Allocate space for return value.
        PushFrame(loc(expr)),        # Create new Frame
        Push(loc(expr), Address(return_instr, loc(expr))),  # Push return Address.
    ]

    for arg in right_exp(expr):  # evaluate parameters (Push),
        instrs.extend(expression_func(arg, symbol_table, stack, expression_func, jump_props))

    # Evaluate primary/left_exp which should be a pointer to function/code
    instrs.extend(expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props))
    assert isinstance(instrs[-1], Load)
    instrs.extend((AbsoluteJump(loc(expr)), return_instr))

    return instrs


def array_subscript(expr, symbol_table, stack, expression_func, jump_props):
    instrs = expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props)
    instrs.extend(expression_func(right_exp(expr), symbol_table, stack, expression_func, jump_props))
    instrs.extend((
        # Calculate Offset.
        Push(loc(expr), size(c_type(right_exp(expr)))),
        Multiply(loc(expr)),
        Add(loc(expr)),
    ))
    if not isinstance(c_type(right_exp(expr)), ArrayType):  # Load if not another ArrayType
        instrs.append(Load(loc(expr), size(c_type(right_exp(expr)))))
    return instrs


# Element selection is a bit tricky, the whole struct will be loaded onto the stack, we need to deallocate it
# and only copy/select the specific value.
def element_selection(expr, symbol_table, stack, expression_func, jump_props):
    instrs = expression_func(left_exp(expr), symbol_table, stack, expression_func, jump_props)
    instrs.extend((
        Allocate(loc(expr), Integer(-1 * size(c_type(left_exp(expr))), loc(expr))),  # dealloc struct
        LoadStackPointer(loc(expr)),  # Push the current stack pointer.
        # Push the offset of the member in question.
        Push(loc(expr), Integer(struct_member_offset(right_exp(expr), c_type(left_exp(expr))), loc(expr))),
        Add(loc(expr)),  # calculate members address
        Load(loc(expr), size(c_type(expr))),  # Push the value onto the stack.
    ))
    return instrs


def element_section_pointer(expr, symbol_table, stack, expression_func, jump_props):
    instrs = expression_func(expr, symbol_table, stack, expression_func, jump_props)  # Load the value of the pointer
    instrs.extend((
        Push(loc(expr), Integer(struct_member_offset(right_exp(expr), c_type(left_exp(expr))), loc(expr))),
        Add(loc(expr)),
        Load(loc(expr), size(c_type(expr))),
    ))
    return instrs


def postfix_expression(expr, symbol_table, stack, expression_func, jump_props):
    return postfix_expression.rules[type(expr)](expr, symbol_table, stack, expression_func, jump_props)
postfix_expression.rules = {
    PostfixIncrementExpression: lambda *args: inc_dec(1, *args),
    PostfixDecrementExpression: lambda *args: inc_dec(-1, *args),
    FunctionCallExpression: function_call,
    ArraySubscriptingExpression: array_subscript,
    ElementSelectionExpression: element_selection,
    ElementSelectionThroughPointerExpression: element_section_pointer
}
postfix_expression.late_instrs = []  # Used to inject late instructions after expression is complete.
