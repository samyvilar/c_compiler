__author__ = 'samyvilar'

from itertools import chain
from collections import defaultdict

from front_end.loader.locations import loc

from sequences import reverse

from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.types import c_type, ArrayType, FunctionType, PointerType, void_pointer_type, StringType, VoidType

from back_end.virtual_machine.instructions.architecture import Push, Address, Load, Set
from back_end.virtual_machine.instructions.architecture import Integer, Multiply, Add, Pass
from back_end.virtual_machine.instructions.architecture import LoadStackPointer
from back_end.virtual_machine.instructions.architecture import SetBaseStackPointer, allocate
from back_end.virtual_machine.instructions.architecture import AbsoluteJump, dup, push_frame, pop_frame
from back_end.emitter.c_types import size, struct_member_offset


def inc_dec(expr, symbol_table, expression_func):
    instrs = chain(  # allocate space for value ...
        allocate(Address(size(c_type(expr)), loc(expr))), expression_func(exp(expr), symbol_table, expression_func)
    )
    temp = next(instrs)
    for instr in instrs:
        yield temp
        temp = instr

    if not isinstance(temp, Load):
        raise ValueError('{l} Expected load instr got {g}'.format(l=loc(temp), g=temp))
    assert size(c_type(expr)) <= size(void_pointer_type)
    # At this point the address is on the stack and the size of the value is either equal or greater than an address ...
    value = Integer((isinstance(expr, PostfixIncrementExpression) and 1) or -1, loc(expr))
    if isinstance(c_type(expr), PointerType) and not isinstance(c_type(c_type(expr)), VoidType):
        value = Integer(value * size(c_type(c_type(expr))), loc(value))

    # make a copy of the address ...
    for i in chain(dup(Integer(size(void_pointer_type), loc(expr)))):
        yield i
    yield temp  # load the value of the expression ...

    # copy/move the value to the previously allocated memory block ...
    yield LoadStackPointer(loc(expr))
    yield Push(loc(expr), Address(1 + size(void_pointer_type) + size(c_type(expr)), loc(expr)))  # skip prev mem & curr
    yield Add(loc(expr))
    yield Set(loc(expr), size(c_type(expr)))

    # Increment or Decrement the value
    assert size(c_type(expr)) == size(value)
    yield Push(loc(expr), value)  # Push either -1 or 1
    yield Add(loc(expr))

    yield LoadStackPointer(loc(expr))  # copy pointer to the bottom of the stack
    yield Push(loc(expr), Address(1 + size(c_type(expr)), loc(expr)))
    yield Add(loc(expr))
    yield Load(loc(expr), Integer(size(void_pointer_type)))
    yield Set(loc(expr), Integer(size(c_type(expr))))
    # deallocate copied address and incremented value ....
    for instr in allocate(Address(-(size(void_pointer_type) + size(c_type(expr))), loc(expr))):
        yield instr


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
    return_instr = Pass(l)  # once the function returns remove created frame

    def _size(ctype):
        return _size.rules[type(ctype)](ctype)
    _size.rules = defaultdict(lambda: size)
    _size.rules.update(
        {   # calling size() on array types will yield their total byte size but they are passed as pointers
            ArrayType: lambda ctype: size(void_pointer_type),
            StringType: lambda ctype: size(void_pointer_type),
            VoidType: lambda ctype: Integer(0, loc(expr)),
        }
    )
    total_size_of_arguments = sum(_size(c_type(e)) for e in right_exp(expr))
    return chain(
        # Allocate space for return value, save frame.
        allocate(Address(_size(c_type(expr)), l)),
        push_frame(l),
        # Push arguments in reverse order (right to left) ...
        chain.from_iterable(reverse(expression_func(arg, symbol_table, expression_func) for arg in right_exp(expr))),
        (
            LoadStackPointer(l),  # Pointer to location where to store return values ...
            Push(l, Address(total_size_of_arguments + 1 + 2 * _size(void_pointer_type), l)),  # skip prev stack, base pt
            Add(l),
            Push(l, Address(return_instr, l)),  # make callee aware of were to return to.
        ),
        expression_func(left_exp(expr), symbol_table, expression_func),   # load callee address
        (   # calculate new base stack pointer excluding the callees address ...
            LoadStackPointer(l),
            Push(l, Address(size(void_pointer_type))),
            Add(l),  # Absolute Jump will pop the address from the stack ... leaving the frame empty ...
            SetBaseStackPointer(l),  # give callee a new frame to work with ...
            AbsoluteJump(l),
            return_instr,
        ),
        # Pop Frame, first stack pointer then base stack pointer
        pop_frame(Address(total_size_of_arguments, l), size(void_pointer_type)),
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
    if isinstance(value, Load):  # if we are loading the structure then just calculate the elements offset ...
        for i in element_instrs(c_type(left_exp(expr)), right_exp(expr), loc(expr)):
            yield i
    else:  # otherwise the structure was just pushed on to the stack ...
        yield value
        struct_size = size(c_type(left_exp(expr)))
        # if we are referencing an array type member its size is the size of a pointer ...
        member_size = size(void_pointer_type) if isinstance(c_type(expr), ArrayType) else size(c_type(expr))
        yield LoadStackPointer(loc(expr))
        # calculate member offset address, assuming the base_address is at stack_ptr + 1
        yield Push(loc(expr), Address(struct_member_offset(c_type(left_exp(expr)), right_exp(expr)) + 1, loc(expr)))
        yield Add(loc(expr))  # calculate starting/base address of structure
        if not isinstance(c_type(expr), ArrayType):  # Load the value if its not an array, otherwise just lease the addr
            yield Load(loc(expr), member_size)

        # move/cpy the value to the top bypassing itself and the struct ...
        yield LoadStackPointer(loc(expr))
        yield Push(loc(expr), Address(struct_size + member_size, loc(expr)))
        yield Add(loc(expr))
        yield Set(loc(expr), size(c_type(expr)))
        for instr in allocate(Address(-(struct_size - member_size), loc(expr))):   # remove all extra values ...
            yield instr


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