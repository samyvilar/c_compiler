__author__ = 'samyvilar'

from itertools import chain, imap

from front_end.loader.locations import loc

from sequences import reverse, all_but_last

from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.types import c_type, ArrayType, FunctionType, PointerType, void_pointer_type, StringType, VoidType

from back_end.virtual_machine.instructions.architecture import Address, add, set_instr, load_instr, load_stack_pointer
from back_end.virtual_machine.instructions.architecture import Pass, multiply, is_load, Load
from back_end.virtual_machine.instructions.architecture import set_base_stack_pointer, allocate
from back_end.virtual_machine.instructions.architecture import absolute_jump, push_frame, pop_frame, push
from back_end.emitter.c_types import size, struct_member_offset

from back_end.virtual_machine.instructions.architecture import postfix_update

default_last_object = object()


def inc_dec(expr, symbol_table, expression_func):
    assert size(c_type(expr)) == size(void_pointer_type)

    # At this point the address is on the stack and the size of the value is equal to an address ...
    value = (isinstance(expr, PostfixIncrementExpression) and 1) or -1
    if isinstance(c_type(expr), PointerType) and not isinstance(c_type(c_type(expr)), VoidType):
        value *= size(c_type(c_type(expr)))

    return postfix_update(
        all_but_last(expression_func(exp(expr), symbol_table, expression_func), Load), value, loc(expr)
    )


def func_type(expr):
    if isinstance(c_type(expr), FunctionType):
        return c_type(expr)
    elif isinstance(c_type(expr), PointerType) and isinstance(c_type(c_type(expr)), FunctionType):
        return c_type(c_type(expr))
    else:
        raise ValueError('{l} Expected FunctionType or Pointer to FunctionType got {g}'.format(
            l=loc(expr), g=c_type(expr)
        ))


def function_call(expr, symbol_table, expression_func):
    l = loc(expr)
    return_instr = Pass(l)  # once the function returns remove created frame

    _size = lambda ctype: size(ctype, overrides={
        ArrayType: size(void_pointer_type),
        StringType: size(void_pointer_type),
        VoidType: 0
    })

    total_size_of_arguments = sum(imap(_size, imap(c_type, right_exp(expr))))
    return chain(
        # Allocate space for return value, save frame.
        allocate(_size(c_type(expr)), l),
        push_frame(
            # Push arguments in reverse order (right to left) ...
            chain.from_iterable(reverse(expression_func(a, symbol_table, expression_func) for a in right_exp(expr))),
            location=l,
            total_size_of_arguments=total_size_of_arguments,
        ),
        push(Address(return_instr, l), l),  # make callee aware of were to return to.
        absolute_jump(
            chain(
                expression_func(left_exp(expr), symbol_table, expression_func),   # load callee address
                # calculate new base stack pointer excluding the callees address ...
                # give the callee a new frame... if we where to reset the base stack before evaluating the left_expr
                # we run the risk of failing to properly load function pointers that have being locally defined ...
                set_base_stack_pointer(add(load_stack_pointer(l), push(size(void_pointer_type), l), l), l)
            ),
            l
        ),
        (return_instr,),
        # Pop Frame, first stack pointer then base stack pointer
        pop_frame(l),
    )


def array_subscript(expr, symbol_table, expression_func):
    l = loc(expr)
    addr_instrs = add(
        expression_func(left_exp(expr), symbol_table, expression_func),
        multiply(expression_func(right_exp(expr), symbol_table, expression_func), push(size(c_type(expr)), l), l),
        l,
    )
    return addr_instrs if isinstance(c_type(expr), ArrayType) else load_instr(addr_instrs, size(c_type(expr)), l)


def element_instrs(struct_obj, member_name, location, load_instrs=iter(())):
    addr_instr = add(
        load_instrs,
        push(struct_member_offset(struct_obj, member_name), location),
        location
    )
    return addr_instr if isinstance(c_type(struct_obj.members[member_name]), ArrayType) \
        else load_instr(addr_instr, size(c_type(struct_obj.members[member_name])), location)


# Element selection is a bit tricky, the whole struct will be loaded onto the stack, we need to deallocate it
# and only copy/select the specific value.
def element_selection(expr, symbol_table, expression_func):
    instrs = expression_func(left_exp(expr), symbol_table, expression_func)
    # if we are loading the structure then just remove Load, calculate the elements offset and Load...
    if is_load(instrs):
        return element_instrs(
            c_type(left_exp(expr)),
            right_exp(expr),
            loc(expr),
            load_instrs=all_but_last(instrs, Load, loc(expr))
        )

    struct_size = size(c_type(left_exp(expr)))
    # if we are referencing an array type member its size is the size of a pointer ...
    member_size = size(size(c_type(expr)), overrides={
        StringType: size(void_pointer_type), ArrayType: size(void_pointer_type)
    })
    addr_instr = add(
        load_stack_pointer(loc(expr)),
        push(struct_member_offset(c_type(left_exp(expr)), right_exp(expr)) + 1, loc(expr)),
        loc(expr)
    )

    return chain(
        set_instr(
            chain(
                load_instr(addr_instr, member_size, loc(expr))
                if not isinstance(c_type(expr), ArrayType)
                else addr_instr,
                add(load_stack_pointer(loc(expr)), push(struct_size + member_size, loc(expr)), loc(expr)),
            ),
            size(c_type(expr)),
            loc(expr)
        ),
        allocate(-(struct_size - member_size), loc(expr))
    )


def element_section_pointer(expr, symbol_table, expression_func):
    return element_instrs(
        c_type(c_type(left_exp(expr))),
        right_exp(expr),
        loc(expr),
        load_instrs=expression_func(left_exp(expr), symbol_table, expression_func)
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