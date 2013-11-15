__author__ = 'samyvilar'

from itertools import chain, imap

from front_end.loader.locations import loc, LocationNotSet

from sequences import reverse, all_but_last

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.ast.expressions import IdentifierExpression
from front_end.parser.types import c_type, ArrayType, FunctionType, PointerType, void_pointer_type, StringType


from back_end.virtual_machine.instructions.architecture import Address, add, set_instr, load_instr, load_stack_pointer
from back_end.virtual_machine.instructions.architecture import Pass, multiply, is_load, Load, Offset
from back_end.virtual_machine.instructions.architecture import set_base_stack_pointer, allocate, relative_jump
from back_end.virtual_machine.instructions.architecture import absolute_jump, push
from back_end.virtual_machine.instructions.architecture import set_base_stack_pointer, set_stack_pointer
from back_end.virtual_machine.instructions.architecture import load_base_stack_pointer
from back_end.emitter.c_types import size, size_extended, struct_member_offset, function_operand_type_sizes

from back_end.virtual_machine.instructions.architecture import postfix_update

default_last_object = object()


def inc_dec(expr, symbol_table, expression_func):
    assert size(c_type(expr)) == size(void_pointer_type)

    # At this point the address is on the stack and the size of the value is equal to an address ...
    value = (isinstance(expr, PostfixIncrementExpression) and 1) or -1
    if isinstance(c_type(expr), PointerType):
        value *= size_extended(c_type(c_type(expr)))

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


def call_function(function_call_expr, symbol_table, expression_func):
    l, expr = loc(function_call_expr), left_exp(function_call_expr)
    return chain(  # if expression is a simple identifier of function type, no need for AbsoluteJump,
                   # just faster RelativeJump.
        set_base_stack_pointer(load_stack_pointer(l), l),
        relative_jump(Offset(symbol_table[name(expr)].get_address_obj(l).obj, l), l),
    ) if isinstance(expr, IdentifierExpression) and isinstance(c_type(expr), FunctionType) else absolute_jump(
        chain(
            expression_func(expr, symbol_table, expression_func),   # load callee address
            # calculate new base stack pointer excluding the callees address ...
            # give the callee a new frame... if we where to reset the base stack before evaluating the left_expr
            # we run the risk of failing to properly load function address if it was store as a local function pointer
            set_base_stack_pointer(add(load_stack_pointer(l), push(size(void_pointer_type), l), l), l)
        ),
        l
    )


def push_frame(
        arguments_instrs=(),
        location=LocationNotSet,
        total_size_of_arguments=0,
        omit_pointer_for_return_value=False,
):
    return chain(
        load_base_stack_pointer(location),

        arguments_instrs,

        # Pointer to where to store return values, if applicable (ie non-zero return size)...
        () if omit_pointer_for_return_value else
        add(
            # calculate pointer for ret value, excluding previous pointers ...
            load_stack_pointer(location),
            push((total_size_of_arguments + (2 * size(void_pointer_type))), location),
            location
        )
    )


def pop_frame(location=LocationNotSet, total_size_of_arguments=0, omit_pointer_for_return_value=False):
    # return pop_frame_instr(location)  # method 1 requires special instruction that has to manage blocks

    # method 2 (5 instructions LoadBaseStackPtr, Push, Add, SetStackPtr, SetBaseStackPtr)
    # method 2 seems to be faster even though it has an extra instruction compare to method 3, not really sure why ...
    return set_base_stack_pointer(
        set_stack_pointer(
            add(
                # remove parameters and ret addr ...
                load_base_stack_pointer(location),
                push(
                    total_size_of_arguments +  # remove parameters ...
                    size(void_pointer_type) +  # remove ret address pointer ...
                    # remove ptr for ret value if it was emitted ...
                    ((not omit_pointer_for_return_value) * size(void_pointer_type)),
                    location
                ),
                location
            ),
            location
        ),
        location
    )

    # method 3 (4 instructions (LoadBaseStackPtr, SetStackPtr, Allocate, SetBaseStackPtr))
    # return set_base_stack_pointer(
    #     chain(
    #         set_stack_pointer(load_base_stack_pointer(location), location),  # load callees base pointer ...
    #         allocate(  # de-allocate everything ...
    #             -(
    #                 total_size_of_arguments +  # remove parameters ...
    #                 size(void_pointer_type) +  # remove ret address pointer ...
    #                 # remove ptr for ret value if it was emitted ...
    #                 ((not omit_pointer_for_return_value) * size(void_pointer_type))
    #             ),
    #             location
    #         )
    #     ),
    #     location
    # )


def function_call(expr, symbol_table, expression_func):
    l, return_instr = loc(expr), Pass(loc(expr))
    total_size_of_arguments = sum(imap(function_operand_type_sizes, imap(c_type, right_exp(expr))))
    omit_pointer_for_return_value = not function_operand_type_sizes(c_type(expr))  # or isinstance(expr, Statement)

    # if omit_pointer_for_return_value:
    #     # if the function call is a statement or its return type has zero size.
    #     # lets do some minor optimizations, since function calls already quite expensive as it is.
    #     expr.c_type = VoidType(loc(l))  # change the return type of the expression to void.
    #     # since we are omitting the return pointer, we have to update the parameter offsets, since they are calculated
    #     # assuming that a return pointer is added ...
    #     # all sets should be decrease by size(void_pointer) for this expression but this may not be true for other
    #     # function call expressions that may actually use the return value of this as such ... :(
    # we would need to check if the functions return value is ALWAYS ignored if and only if then can we omit
    # the return pointer for know its only applicable for for functions whose return size is zero ...
    # TODO: post-compilation optimization that optimizes functions whose returned values is ALWAYS ignored.

    return chain(
        # Allocate space for return value, save frame.
        allocate(function_operand_type_sizes(c_type(expr)), l),
        push_frame(
            # Push arguments in reverse order (right to left) ...
            chain.from_iterable(reverse(expression_func(a, symbol_table, expression_func) for a in right_exp(expr))),
            location=l,
            total_size_of_arguments=total_size_of_arguments,
            omit_pointer_for_return_value=omit_pointer_for_return_value
        ),
        push(Address(return_instr, l), l),  # make callee aware of were to return to.
        call_function(expr, symbol_table, expression_func),
        (return_instr,),
        # Pop Frame, first stack pointer then base stack pointer
        pop_frame(
            location=l,
            total_size_of_arguments=total_size_of_arguments,
            omit_pointer_for_return_value=omit_pointer_for_return_value
        )
    )


def array_subscript(expr, symbol_table, expression_func):
    l = loc(expr)
    addr_instrs = add(
        expression_func(left_exp(expr), symbol_table, expression_func),
        multiply(
            expression_func(right_exp(expr), symbol_table, expression_func),
            push(size(c_type(expr)), l),
            l
        ),
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
        push(
            (struct_member_offset(c_type(left_exp(expr)), right_exp(expr)) + size(void_pointer_type)),
            loc(expr)
        ),
        loc(expr)
    )

    return chain(
        set_instr(
            chain(
                load_instr(addr_instr, member_size, loc(expr)) if not isinstance(c_type(expr), ArrayType)
                else addr_instr,
                add(load_stack_pointer(loc(expr)), push((struct_size + member_size), loc(expr)), loc(expr)),
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