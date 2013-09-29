
#include "cpu.h"
#include "kernel.h"
#include <stdio.h>


const word_type _instr_sizes_[256] = {
        INSTRUCTION_SIZES
};
#define INSTR_SIZE(instr_id) (_instr_sizes_[(instr_id)])
//inline word_type INSTR_SIZE(word_type instr_id) { return _instr_sizes_[instr_id]; }

const word_type _instr_pointer_updates_[] = {
        INSTRUCTION_SIZES,
        // The following instructions will manually update the instruction pointer.
        [ABSOLUTE_JUMP] = 0,
        [RELATIVE_JUMP] = 0,
        [JUMP_FALSE] = 0,
        [JUMP_TRUE] = 0,
        [JUMP_TABLE] = 0,
        [SYSTEM_CALL] = 0,
};

#define inrement_instr_pointer(cpu, instr) (update_instr_pointer(cpu, _instr_pointer_updates_[instr]))

const char *_instr_names_[] = {
        [0 ... 255] = "INVALID INSTRUCTION",
        [HALT] = "HALT",
        [PASS] = "PASS",
        [PUSH] = "PUSH",
        [POP] = "POP",
        [LOAD] = "LOAD",
        [SET] = "SET",
        [LOAD_BASE_STACK_POINTER] = "LOAD_BASE_STACK_POINTER",
        [SET_BASE_STACK_POINTER] = "SET_BASE_STAC_POINTER",
        [LOAD_STACK_POINTER] = "LOAD_STACK_POINTER",
        [SET_STACK_POINTER] = "SET_STACK_POINTER",
        [ADD] = "ADD",
        [SUBTRACT] = "SUBTRACT",
        [MULTIPLY] = "MULTIPLY",
        [DIVIDE] = "DIVIDE",
        [MOD] = "MOD",
        [SHIFT_LEFT] = "SHIFT_LEFT",
        [SHIFT_RIGHT] = "SHIFT_RIGHT",
        [OR] = "OR",
        [AND] = "AND",
        [NOT] = "NOT",
        [ADD_FLOAT] = "ADD_FLOAT",
        [SUBTRACT_FLOAT] = "SUBTRACT_FLOAT",
        [MULTIPLY_FLOAT] = "MULTIPLY_FLOAT",
        [DIVIDE_FLOAT] = "DIVIDE_FLOAT",
        [CONVERT_TO_FLOAT] = "CONVERT_TO_FLOAT",
        [CONVERT_TO_INTEGER] = "CONVERT_TO_INTEGER",
        [ABSOLUTE_JUMP] = "ABSOLUTE_JUMP",
        [JUMP_FALSE] = "JUMP_FALSE",
        [JUMP_TRUE] = "JUMP_TRUE",
        [JUMP_TABLE] = "JUMP_TABLE",
        [RELATIVE_JUMP] = "RELATIVE_JUMP",
        [LOAD_ZERO_FLAG] = "LOAD_ZERO_FLAG",
        [LOAD_CARRY_BORROW_FLAG] = "LOAD_CARRY_BORROW_FLAG",
        [LOAD_MOST_SIGNIFICANT_BIT_FLAG] = "LOAD_MOST_SIGNIFICANT_BIT_FLAG",
        [SYSTEM_CALL] = "SYSTEM_CALL"
};
#define INSTR_NAME(instr_id) _instr_names_[instr_id]


////inline void push_word(word_type word, cpu_type *cpu, virtual_memory_type *mem, struct kernel_type *os)
////{
////    set_word(mem, stack_pointer(cpu), word);
////    set_stack_pointer(cpu, (stack_pointer(cpu) - WORD_SIZE));
////}
//#define push_word(word, cpu, mem, os) (set_word(mem, stack_pointer(cpu), word), set_stack_pointer(cpu, (stack_pointer(cpu) - WORD_SIZE)))
//
////inline word_type pop_word(cpu_type *cpu, virtual_memory_type *mem, struct kernel_type *os)
////{
////    set_stack_pointer(cpu, (stack_pointer(cpu) + WORD_SIZE));
////    return get_word(mem, stack_pointer(cpu));
////}
//#define pop_word(cpu, mem, os) (set_stack_pointer(cpu, (stack_pointer(cpu) + WORD_SIZE)), get_word(mem, stack_pointer(cpu)))

INLINE_FUNC_SIGNATURE(invalid_instr) {
    printf("Invalid instruction " WORD_PRINTF_FORMAT "@" WORD_PRINTF_FORMAT ", halting!\n", get_word(mem, instr_pointer(cpu)), instr_pointer(cpu));
    set_word(mem, instr_pointer(cpu) + 1, HALT);  // set next instruction to halt machine.
}
INLINE_FUNC_SIGNATURE(system_call) {  calls(os)[(unsigned char)pop_word(cpu, mem, os)](cpu, mem, os);  }
INLINE_FUNC_SIGNATURE(pass)  {}
INLINE_FUNC_SIGNATURE(push)  { push_word(operand(cpu, mem, 0), cpu, mem, os); }
INLINE_FUNC_SIGNATURE(pop)   { (void)pop_word(cpu, mem, os); }
INLINE_FUNC_SIGNATURE(load)
{
    word_type dest = pop_word(cpu, mem, os), amount = operand(cpu, mem, 0);
    while (amount--)
        push_word(get_word(mem, dest + amount), cpu, mem, os);
}
INLINE_FUNC_SIGNATURE(set)
{
    word_type dest = pop_word(cpu, mem, os), amount = operand(cpu, mem, 0);
    word_type stack_ptr = stack_pointer(cpu) + 1;
    while (amount--)
        set_word(mem, dest, get_word(mem, stack_ptr)), dest++, stack_ptr++;
}
INLINE_FUNC_SIGNATURE(load_base_stack_pointer) {    push_word(base_pointer(cpu), cpu, mem, os);     }
INLINE_FUNC_SIGNATURE(set_base_stack_pointer)  {    set_base_pointer(cpu, pop_word(cpu, mem, os));  }
INLINE_FUNC_SIGNATURE(load_stack_pointer)      {    push_word(stack_pointer(cpu), cpu, mem, os);    }
INLINE_FUNC_SIGNATURE(_set_stack_pointer)      {    set_stack_pointer(cpu, pop_word(cpu, mem, os)); }

#define MSB(value) (value  >> (word_type)((8*sizeof(word_type)) - 1))
#define BINARY_INTEGRAL_INSTRUCTION(name, _o_) \
INLINE_FUNC_SIGNATURE(name) \
{ \
    register word_type   \
        oper_2 = pop_word(cpu, mem, os),    \
        oper_1 = pop_word(cpu, mem, os);    \
    register word_type result = oper_1 _o_ oper_2; \
    push_word(result, cpu, mem, os); \
    set_zero_flag(cpu, !result);    \
    set_most_significant_bit_flag(cpu, MSB(result));    \
    /* overflow_flag = !(MSB(oper_1) ^ MSB(oper_2)) & (MSB(result) ^ MSB(oper_1)) */\
}

INLINE_FUNC_SIGNATURE(_add) {
    register word_type
        oper_2 = pop_word(cpu, mem, os),
        oper_1 = pop_word(cpu, mem, os);
    register word_type result = oper_1 + oper_2;
    push_word(result, cpu, mem, os);
    set_zero_flag(cpu, !result);
    set_most_significant_bit_flag(cpu, MSB(result));
    set_carry_borrow_flag(cpu, (result < oper_1) & (result < oper_2));

}
INLINE_FUNC_SIGNATURE(_sub)  {
    register word_type
            oper_2 = pop_word(cpu, mem, os),
            oper_1 = pop_word(cpu, mem, os);
    register word_type result = oper_1 - oper_2;
    push_word(result, cpu, mem, os);
    set_zero_flag(cpu, !result);
    set_most_significant_bit_flag(cpu, MSB(result));
    set_carry_borrow_flag(cpu, (result > oper_1) & (result > oper_2));
}
BINARY_INTEGRAL_INSTRUCTION(_mult, *)
BINARY_INTEGRAL_INSTRUCTION(_div, /)
BINARY_INTEGRAL_INSTRUCTION(_mod, %)
BINARY_INTEGRAL_INSTRUCTION(_shift_left, <<)
BINARY_INTEGRAL_INSTRUCTION(_shift_right, >>)
BINARY_INTEGRAL_INSTRUCTION(_or, |)
BINARY_INTEGRAL_INSTRUCTION(_and, &)
BINARY_INTEGRAL_INSTRUCTION(_xor, ^)

INLINE_FUNC_SIGNATURE(_not) { push_word(~pop_word(cpu, mem, os), cpu, mem, os);   }

#define BINARY_FLOATING_INSTRUCTION(name, _o_) INLINE_FUNC_SIGNATURE(name) \
{  \
    float_type oper_2 = word_as_float(pop_word(cpu, mem, os)), oper_1 = word_as_float(pop_word(cpu, mem, os)); \
    float_type result = oper_1 _o_ oper_2; \
    push_word(*(word_type *)&result, cpu, mem, os); \
    set_zero_flag(cpu, result == 0.0); \
    set_most_significant_bit_flag(cpu, result < 0.0); \
}
BINARY_FLOATING_INSTRUCTION(add_float, +)
BINARY_FLOATING_INSTRUCTION(sub_float, -)
BINARY_FLOATING_INSTRUCTION(mult_float, *)
BINARY_FLOATING_INSTRUCTION(div_float, /)

INLINE_FUNC_SIGNATURE(conv_to_float) {
    //printf("%f\n", ((double)(signed_word_type)pop_word(cpu, mem, os)));
    register float_type value = (float_type)(signed_word_type)pop_word(cpu, mem, os);
    push_word(float_as_word(value), cpu, mem, os);
}

INLINE_FUNC_SIGNATURE(conv_to_float_from_unsigned) {
    register float_type value = (float_type)pop_word(cpu, mem, os);
    push_word(float_as_word(value), cpu, mem, os);
}

INLINE_FUNC_SIGNATURE(conv_to_int)  {
//    push_word((word_type)(*(double *)&word), cpu, mem, os); // reinterpret as double then conv to corresponding integer ...
    register word_type value = (word_type) word_as_float(pop_word(cpu, mem, os));
    push_word(value, cpu, mem, os);
}

INLINE_FUNC_SIGNATURE(abs_jump)   {  set_instr_pointer(cpu, pop_word(cpu, mem, os));  }
INLINE_FUNC_SIGNATURE(rel_jump)   {  update_instr_pointer(cpu, (operand(cpu, mem, 0)));  }
INLINE_FUNC_SIGNATURE(jump_false) {
    update_instr_pointer(cpu, (pop_word(cpu, mem, os) ? INSTR_SIZE(JUMP_TRUE) : operand(cpu, mem, 0)));
}
INLINE_FUNC_SIGNATURE(jump_true)  {
    update_instr_pointer(cpu, (pop_word(cpu, mem, os) ? operand(cpu, mem, 0) : INSTR_SIZE(JUMP_TRUE)));
}
INLINE_FUNC_SIGNATURE(jump_table)  {
    word_type
            number_of_cases = operand(cpu, mem, 0),
            default_offset = operand(cpu, mem, 1),
            value = pop_word(cpu, mem, os),
            cases = instr_pointer(cpu) + 2 + INSTR_SIZE(PASS);

    while (number_of_cases--)
    {
        if (get_word(mem, cases) == value)
        {
            default_offset = get_word(mem, cases + 1);
            break ;
        }
        cases += 2;
    }
    set_instr_pointer(cpu, instr_pointer(cpu) + default_offset);
}
INLINE_FUNC_SIGNATURE(load_zero_flag) {  push_word(zero_flag(cpu), cpu, mem, os);  }
INLINE_FUNC_SIGNATURE(load_carry_borrow_flag) {  push_word(carry_borrow_flag(cpu), cpu, mem, os); }
INLINE_FUNC_SIGNATURE(load_most_significant_bit_flag) { push_word(most_significant_bit_flag(cpu), cpu, mem, os); }


FUNC_SIGNATURE((*instrs[256])) = {
        [0 ... 255] = invalid_instr,
        [HALT] = pass,  // evaluate will halt
        [PASS] = pass,
        [PUSH] = push,
        [POP] = pop,
        [LOAD] = load,
        [SET] = set,
        [LOAD_BASE_STACK_POINTER] = load_base_stack_pointer,
        [SET_BASE_STACK_POINTER] = set_base_stack_pointer,
        [LOAD_STACK_POINTER] = load_stack_pointer,
        [SET_STACK_POINTER] = _set_stack_pointer,
        [ADD] = _add,
        [SUBTRACT] = _sub,
        [MULTIPLY] = _mult,
        [DIVIDE] = _div,
        [MOD] = _mod,
        [SHIFT_LEFT] = _shift_left,
        [SHIFT_RIGHT] = _shift_right,
        [OR] = _or,
        [AND] = _and,
        [XOR] = _xor,
        [NOT] = _not,
        [ADD_FLOAT] = add_float,
        [SUBTRACT_FLOAT] = sub_float,
        [MULTIPLY_FLOAT] = mult_float,
        [DIVIDE_FLOAT] = div_float,
        [CONVERT_TO_FLOAT] = conv_to_float,
        [CONVERT_TO_FLOAT_FROM_UNSIGNED] = conv_to_float_from_unsigned,
        [CONVERT_TO_INTEGER] = conv_to_int,
        [ABSOLUTE_JUMP] = abs_jump,
        [RELATIVE_JUMP] = rel_jump,
        [JUMP_TRUE] = jump_true,
        [JUMP_FALSE] = jump_false,
        [JUMP_TABLE] = jump_table,
        [LOAD_CARRY_BORROW_FLAG] = load_carry_borrow_flag,
        [LOAD_MOST_SIGNIFICANT_BIT_FLAG] = load_most_significant_bit_flag,
        [LOAD_ZERO_FLAG] = load_zero_flag,
        [SYSTEM_CALL] = system_call
};


INLINE_FUNC_SIGNATURE(evaluate) {
    register unsigned char instr_id;
    do
    {
        instr_id = (unsigned char)get_word(mem, instr_pointer(cpu));
        instrs[instr_id](cpu, mem, os);
        inrement_instr_pointer(cpu, instr_id);
    } while (instr_id != HALT);
}