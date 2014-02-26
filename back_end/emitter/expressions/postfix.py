__author__ = 'samyvilar'

from itertools import chain, imap, izip, repeat

from front_end.loader.locations import loc, LocationNotSet

from utils.sequences import reverse, all_but_last
from utils.rules import set_rules, rules

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression, left_exp, right_exp
from front_end.parser.ast.expressions import FunctionCallExpression, ArraySubscriptingExpression, exp
from front_end.parser.ast.expressions import ElementSelectionExpression, ElementSelectionThroughPointerExpression
from front_end.parser.ast.expressions import IdentifierExpression
from front_end.parser.types import c_type, ArrayType, FunctionType, PointerType, void_pointer_type, StringType
from front_end.parser.types import IntegralType, VoidType


from back_end.virtual_machine.instructions.architecture import Address, add, set_instr, load, load_stack_pointer
from back_end.virtual_machine.instructions.architecture import Pass, multiply, is_load, Loads, Offset
from back_end.virtual_machine.instructions.architecture import set_base_stack_pointer, allocate, relative_jump
from back_end.virtual_machine.instructions.architecture import absolute_jump, push
from back_end.virtual_machine.instructions.architecture import set_stack_pointer
from back_end.virtual_machine.instructions.architecture import load_base_stack_pointer
from back_end.emitter.c_types import size, size_extended, struct_member_offset, size_arrays_as_pointers

from back_end.virtual_machine.instructions.architecture import get_postfix_update

from back_end.emitter.expressions.cast import cast


def inc_dec(expr, symbol_table):
    assert not isinstance(c_type(expr), ArrayType) and isinstance(c_type(expr), IntegralType)
    value = rules(inc_dec)[type(expr)]
    if isinstance(c_type(expr), PointerType):
        value *= size_extended(c_type(c_type(expr)))

    return get_postfix_update(size(c_type(expr)))(
        all_but_last(symbol_table['__ expression __'](exp(expr), symbol_table), Loads, loc(expr)),
        value,
        loc(expr)
    )
set_rules(inc_dec, ((PostfixIncrementExpression, 1), (PostfixDecrementExpression, -1)))


def func_type(expr):
    if isinstance(c_type(expr), FunctionType):
        return c_type(expr)
    elif isinstance(c_type(expr), PointerType) and isinstance(c_type(c_type(expr)), FunctionType):
        return c_type(c_type(expr))
    else:
        raise ValueError('{l} Expected FunctionType or Pointer to FunctionType got {g}'.format(
            l=loc(expr), g=c_type(expr)
        ))


def call_function(function_call_expr, symbol_table):
    l, expr = loc(function_call_expr), left_exp(function_call_expr)
    return chain(  # if expression is a simple identifier of function type, no need for AbsoluteJump, use RelativeJump
        set_base_stack_pointer(load_stack_pointer(l), l),
        relative_jump(Offset(symbol_table[name(expr)].get_address_obj(l).obj, l), l),
    ) if isinstance(expr, IdentifierExpression) and isinstance(c_type(expr), FunctionType) else absolute_jump(
        chain(
            symbol_table['__ expression __'](expr, symbol_table),   # load callee address
            # calculate new base stack pointer excluding the callees address ...
            # give the callee a new frame... if we where to reset the base stack ptr before evaluating the left_expr
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
        load_base_stack_pointer(location),  # save previous base stack pointer ...
        arguments_instrs,
        # Pointer to where to store return values, if applicable (ie non-zero return size)...
        () if omit_pointer_for_return_value else
        # calculate pointer for ret value, excluding base pointer ...
        add(load_stack_pointer(location), push((total_size_of_arguments + size(void_pointer_type)), location), location)
    )


def pop_frame(location=LocationNotSet, total_size_of_arguments=0, omit_pointer_for_return_value=False):
    # return pop_frame_instr(location)  # method 1 requires special instruction that has to manage blocks

    # method 2 (5 instructions LoadBaseStackPtr, Push, Add, SetStackPtr, SetBaseStackPtr)
    # method 2 seems to be faster even though it has an extra instruction compare to method 3,
    # not really sure why ... probably because the optimizer is removing some of them

    return set_base_stack_pointer(
        set_stack_pointer(
            add(
                # remove parameters and ret addr ...
                load_base_stack_pointer(location),
                push(    # remove parameters, ret address pointer, and ptr for ret value if it was emitted ...
                    sum((
                        total_size_of_arguments, size(void_pointer_type),
                        (not omit_pointer_for_return_value) * size(void_pointer_type))),
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


def function_call(expr, symbol_table):
    assert not isinstance(c_type(expr), ArrayType)
    l, return_instr = loc(expr), Pass(loc(expr))
    total_size_of_arguments = sum(imap(size_arrays_as_pointers, imap(c_type, right_exp(expr))))
    return_size = size(c_type(expr), overrides={VoidType: 0})
    omit_pointer_for_return_value = not return_size

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
    expression = symbol_table['__ expression __']
    return chain(
        # Allocate space for return value, save frame.
        allocate(return_size, l),
        push_frame(
            # Push arguments in reverse order (right to left) ...
            chain.from_iterable(imap(expression, reverse(right_exp(expr)), repeat(symbol_table))),
            location=l,
            total_size_of_arguments=total_size_of_arguments,
            omit_pointer_for_return_value=omit_pointer_for_return_value
        ),
        push(Address(return_instr, l), l),  # make callee aware of were to return to.
        call_function(expr, symbol_table),
        (return_instr,),
        # Pop Frame, first stack pointer then base stack pointer
        pop_frame(
            location=l,
            total_size_of_arguments=total_size_of_arguments,
            omit_pointer_for_return_value=omit_pointer_for_return_value
        )
    )


def array_subscript(expr, symbol_table):
    assert isinstance(c_type(left_exp(expr)), PointerType) and isinstance(c_type(right_exp(expr)), IntegralType)
    expression = symbol_table['__ expression __']
    l = loc(expr)
    addr_instrs = add(
        expression(left_exp(expr), symbol_table),
        multiply(
            cast(  # convert right expression to address type in order to properly multiply ...
                expression(right_exp(expr), symbol_table),
                c_type(right_exp(expr)),
                void_pointer_type,
                l
            ),
            push(size(c_type(expr)), l),
            l
        ),
        l,
    )   # Load value unless the return type is also an ArrayTyp
    return addr_instrs if isinstance(c_type(expr), ArrayType) \
        else load(addr_instrs, size_arrays_as_pointers(c_type(expr)), l)


def element_instrs(struct_obj, member_name, location, load_instrs=iter(())):
    instrs = add(load_instrs, push(struct_member_offset(struct_obj, member_name), location), location)
    return instrs if isinstance(c_type(struct_obj.members[member_name]), ArrayType) else \
        load(instrs, size_arrays_as_pointers(c_type(struct_obj.members[member_name])), location)


def element_selection(expr, symbol_table):
    instrs = symbol_table['__ expression __'](left_exp(expr), symbol_table)
    # if we are loading the structure then just remove the Load instr, calculate the elements offset and Load that elem
    if is_load(instrs):
        return element_instrs(
            c_type(left_exp(expr)), right_exp(expr), loc(expr), load_instrs=all_but_last(instrs, Loads, loc(expr))
        )

    struct_size, member_size = size(c_type(left_exp(expr))), size_arrays_as_pointers(c_type(expr))
    addr_instrs = add(  # calculate the loaded structured members address
        load_stack_pointer(loc(expr)),
        push(struct_member_offset(c_type(left_exp(expr)), right_exp(expr)), loc(expr)),
        loc(expr)
    )
    return chain(  # copy the element then move it to the base of the structure and deallocate everything else
        set_instr(
            chain(  # load the value in question if its not an array (which is just an address ...)
                (addr_instrs if isinstance(c_type(expr), ArrayType) else load(addr_instrs, member_size, loc(expr))),
                add(load_stack_pointer(loc(expr)), push((struct_size + member_size), loc(expr)), loc(expr)),
            ),
            member_size,
            loc(expr)
        ),
        allocate(-(struct_size - member_size), loc(expr))  # deallocate structure and copied member (set leaves value)
    )


def element_section_pointer(expr, symbol_table):
    return element_instrs(
        c_type(c_type(left_exp(expr))),
        right_exp(expr),
        loc(expr),
        load_instrs=symbol_table['__ expression __'](left_exp(expr), symbol_table)
    )


def postfix_expression(expr, symbol_table):
    return rules(postfix_expression)[type(expr)](expr, symbol_table)
set_rules(
    postfix_expression,
    (
        (PostfixIncrementExpression, inc_dec),
        (PostfixDecrementExpression, inc_dec),
        (FunctionCallExpression, function_call),
        (ArraySubscriptingExpression, array_subscript),
        (ElementSelectionExpression, element_selection),
        (ElementSelectionThroughPointerExpression, element_section_pointer)
    )
)