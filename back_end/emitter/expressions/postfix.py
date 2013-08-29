__author__ = 'samyvilar'

from itertools import chain
from collections import defaultdict

from front_end.loader.locations import loc

from sequences import reverse

from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.types import c_type, ArrayType, FunctionType, PointerType, void_pointer_type, StringType, VoidType

from back_end.virtual_machine.instructions.architecture import Push, Allocate, PushFrame, PopFrame, Address, Load, Set
from back_end.virtual_machine.instructions.architecture import Integer, Multiply, Add, LoadStackPointer, Dup
from back_end.virtual_machine.instructions.architecture import AbsoluteJump, SetBaseStackPointer, CompoundSet
from back_end.emitter.c_types import size, struct_member_offset


def inc_dec(expr, symbol_table, expression_func):
    instrs = expression_func(exp(expr), symbol_table, expression_func)

    temp = next(instrs)
    for instr in instrs:
        yield temp
        temp = instr

    if not isinstance(temp, Load):
        raise ValueError('{l} Expected load instr got {g}'.format(l=loc(temp), g=temp))
    # At this point the address is on the stack...
    assert size(c_type(expr)) <= size(void_pointer_type)

    value = Integer((isinstance(expr, PostfixIncrementExpression) and 1) or -1, loc(expr))
    if isinstance(c_type(expr), PointerType) and not isinstance(c_type(c_type(expr)), VoidType):
        value = Integer(value * size(c_type(c_type(expr))), loc(value))

    yield Dup(loc(expr), size(void_pointer_type))  # duplicate address
    yield Allocate(loc(expr), Integer(-1 * size(void_pointer_type), loc(expr)))  # deallocate duplicate address
    yield temp  # load value on the stack
    yield Allocate(  # Re-allocate address and any other excess bytes ...
        loc(expr), Integer(size(void_pointer_type) + size(void_pointer_type) - size(c_type(expr)), loc(expr))
    )
    yield Dup(loc(expr), size(void_pointer_type))  # duplicate address
    yield temp
    yield Push(loc(expr), value)  # push 1 or -1
    yield Add(loc(expr))
    yield CompoundSet(loc(expr), size(c_type(expr)))
    yield Allocate(loc(expr), Integer(-1 * size(c_type(expr)), loc(expr)))


def func_type(expr):
    if isinstance(c_type(expr), FunctionType):
        return c_type(expr)
    elif isinstance(c_type(expr), PointerType) and isinstance(c_type(c_type(expr)), FunctionType):
        return c_type(c_type(expr))
    else:
        raise ValueError('{l} Expected FunctionType or Pointer to FunctionType got {g}'.format(
            l=loc(expr), g=c_type(expr)
        ))


# Bug when pushing the new frame, the base pointer is reset losing scope to previous values that may be copied
# over to the next frame!!!!
def function_call(expr, symbol_table, expression_func):
    l = loc(expr)
    _pop_frame_instr = PopFrame(loc(expr))  # once the function returns remove created frame

    def _size(ctype):
        return _size.rules[type(ctype)](ctype)
    _size.rules = defaultdict(lambda: size)
    _size.rules.update(
        {   # calling size() on array types will yield their total byte size but they are passed as pointers
            ArrayType: size(void_pointer_type),
            StringType: size(void_pointer_type),
        }
    )
    return chain(
        # Allocate space for return value, save frame.
        (Allocate(
            l,
            (not isinstance(c_type(expr), VoidType) and size(c_type(expr))) or Integer(0, loc(expr))
        ), PushFrame(l)),
        # Push arguments in reverse order (right to left) ...
        chain.from_iterable(reverse(expression_func(arg, symbol_table, expression_func) for arg in right_exp(expr))),
        (
            LoadStackPointer(l),  # Pointer to location where to store return values ...
            Push(l, Address(sum(_size(c_type(e)) for e in right_exp(expr)) + 1, l)),
            Add(l),
            Push(l, Address(_pop_frame_instr, l)),  # make callee aware of were to return to.
        ),
        expression_func(left_exp(expr), symbol_table, expression_func),   # load callee address
        (
            LoadStackPointer(l),
            Push(l, Address(size(void_pointer_type))),
            Add(l),  # Absolute Jump will pop the address from the stack ...
            SetBaseStackPointer(l),  # give callee a new frame to work with ...

            AbsoluteJump(l),
            _pop_frame_instr
        ),
    )


def array_subscript(expr, symbol_table, expression_func):
    return chain(
        expression_func(left_exp(expr), symbol_table, expression_func),
        expression_func(right_exp(expr), symbol_table, expression_func),
        (
            # Calculate Offset.
            Push(loc(expr), size(c_type(expr))),
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
        member_size = size(void_pointer_type) if isinstance(c_type(expr), ArrayType) else size(c_type(expr))
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