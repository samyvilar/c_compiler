// Instruction IDS ...

#ifndef _CPU_H_
#define _CPU_H_

#include "virtual_memory.h"

#define HALT 255 // -1

#define PUSH 2
#define POP 254 // -2
#define LOAD 3
#define SET 252 // -4

#define LOAD_BASE_STACK_POINTER 7
#define SET_BASE_STACK_POINTER 249 // -7
#define LOAD_STACK_POINTER 8
#define SET_STACK_POINTER 248 // -8

#define ADD 11
#define SUBTRACT 245 // -11

#define MULTIPLY 12
#define DIVIDE 244 // -12

#define MOD 13

#define SHIFT_LEFT 14
#define SHIFT_RIGHT 242 // -14

#define OR 15
#define AND 241 // -15
#define XOR 16
#define NOT 17

#define ADD_FLOAT 18
#define SUBTRACT_FLOAT 238 // -18
#define MULTIPLY_FLOAT 19
#define DIVIDE_FLOAT 237  // -19

#define CONVERT_TO_FLOAT 23
#define CONVERT_TO_FLOAT_FROM_UNSIGNED 24  //
#define CONVERT_TO_INTEGER 233 // -23

#define ABSOLUTE_JUMP 20
#define JUMP_FALSE 21
#define JUMP_TRUE 235 // -21
#define JUMP_TABLE 22
#define RELATIVE_JUMP 33

#define LOAD_ZERO_FLAG 30
#define LOAD_CARRY_BORROW_FLAG 31
#define LOAD_MOST_SIGNIFICANT_BIT_FLAG 32

#define PASS 50
#define SYSTEM_CALL 128


typedef struct cpu_type {
    word_type
    // Since the stack pointer will be the most heavily accessed register better have it as the first one
            stack_pointer,
            base_pointer,
            instr_pointer,
            zero_flag,
            carry_borrow_flag,
            most_significant_bit_flag;
} cpu_type;
// C guarantees that the address of the first member and the struct itself are the same (no need for member calcs)
#define stack_pointer(cpu) (*(word_type *)(cpu))
#define set_stack_pointer(cpu, st_ptr) (stack_pointer(cpu) = (st_ptr))
#define update_stack_pointer(cpu, amount) (stack_pointer(cpu) += (amount))
#define base_pointer(cpu) ((cpu)->base_pointer)
#define set_base_pointer(cpu, b_ptr) (base_pointer(cpu) = (b_ptr))
#define instr_pointer(cpu) ((cpu)->instr_pointer)
#define set_instr_pointer(cpu, ptr) (instr_pointer(cpu) = (ptr))
#define update_instr_pointer(cpu, amount) (instr_pointer(cpu) += (amount))
#define zero_flag(cpu) ((cpu)->zero_flag)
#define set_zero_flag(cpu,  flag) (zero_flag(cpu) = (flag))
#define carry_borrow_flag(cpu) ((cpu)->carry_borrow_flag)
#define set_carry_borrow_flag(cpu, flag) (carry_borrow_flag(cpu) = (flag))
#define most_significant_bit_flag(cpu) ((cpu)->most_significant_bit_flag)
#define set_most_significant_bit_flag(cpu, flag) (most_significant_bit_flag(cpu) = (flag))

#define INSTRUCTION_SIZE 1
#define WIDE_INSTRUCTION_SIZE (2*INSTRUCTION_SIZE)
#define INSTRUCTION_SIZES \
    [0 ... 255] = INSTRUCTION_SIZE, \
    [PUSH] = WIDE_INSTRUCTION_SIZE, \
    [LOAD] = WIDE_INSTRUCTION_SIZE, \
    [SET] = WIDE_INSTRUCTION_SIZE, \
    [JUMP_FALSE] = WIDE_INSTRUCTION_SIZE, \
    [JUMP_TRUE] = WIDE_INSTRUCTION_SIZE, \
    [RELATIVE_JUMP] = WIDE_INSTRUCTION_SIZE

#define operand(cpu, mem, operand_index) get_word(mem, (instr_pointer(cpu) + INSTR_SIZE(PASS)) + operand_index)

struct kernel_type;
#define FUNC_SIGNATURE(func_name) void func_name(cpu_type *cpu, virtual_memory_type *mem, struct kernel_type *os)

#define INLINE_FUNC_SIGNATURE(func_name) INLINE FUNC_SIGNATURE(func_name)


extern const word_type _instr_sizes_[256];
#define INSTR_SIZE(instr_id) (_instr_sizes_[(instr_id)])


#define NO_OPERAND_INSTR(instr) instr
#define SINGLE_OPERAND_INSTR(instr, operand) instr, operand
#define PASS_INSTR() NO_OPERAND_INSTR(PASS)
#define HALT_INSTR() NO_OPERAND_INSTR(HALT)
#define PUSH_INSTR(operand) SINGLE_OPERAND_INSTR(PUSH, operand)
#define POP_INSTR() NO_OPERAND_INSTR(POP)

#define LOAD_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(LOAD, quantity)
#define SET_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET, quantity)

#define LOAD_BASE_STACK_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_BASE_STACK_POINTER)
#define SET_BASE_STACK_POINTER_INSTR(value) PUSH_INSTR(value), SET_BASE_STACK_POINTER
#define LOAD_STACK_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_STACK_POINTER)
#define SET_STACK_POINTER_INSTR(value) PUSH_INSTR(value), SET_STACK_POINTER

#define BINARY_INTEGRAL_INSTR(oper_1, oper_2, instr) PUSH_INSTR(oper_1), PUSH_INSTR(oper_2), NO_OPERAND_INSTR(instr)
#define ADD_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, ADD)
#define SUBTRACT_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, SUBTRACT)
#define MULTIPLY_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, MULTIPLY)
#define DIVIDE_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, DIVIDE)
#define MOD_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, MOD)
#define SHIFT_LEFT_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, SHIFT_LEFT)
#define SHIFT_RIGHT_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, SHIFT_RIGHT)
#define OR_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, OR)
#define AND_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, AND)
#define XOR_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, XOR)
#define NOT_INSTR(value) PUSH_INSTR(value), NOT

//PUSH_INSTR(float_as_word(oper_1)), PUSH_INSTR(float_as_word(oper_2)), NO_OPERAND_INSTR(instr)
#define BINARY_FLOAT_INSTR(oper_1, oper_2, instr) BINARY_INTEGRAL_INSTR(float_as_word(oper_1), float_as_word(oper_2), instr)
#define ADD_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, ADD_FLOAT)
#define SUBTRACT_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, SUBTRACT_FLOAT)
#define MULTIPLY_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, MULTIPLY_FLOAT)
#define DIVIDE_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, DIVIDE_FLOAT)

#define CONVERT_TO_FLOAT_INSTR(oper_1) PUSH_INSTR(oper_1), NO_OPERAND_INSTR(CONVERT_TO_FLOAT)
#define CONVERT_TO_FLOAT_FROM_UNSIGNED_INSTR(oper_1) PUSH_INSTR(oper_1), NO_OPERAND_INSTR(CONVERT_TO_FLOAT_FROM_UNSIGNED)
#define CONVERT_TO_INTEGER_INSTR(oper_1) PUSH_INSTR(float_as_word(oper_1)), NO_OPERAND_INSTR(CONVERT_TO_INTEGER)

#define ABSOLUTE_JUMP_INSTR(addr) PUSH_INSTR(addr), ABSOLUTE_JUMP

#define ADDRESS_OFFSET(instr, offset) ((offset) + INSTR_SIZE(instr))
#define RELATIVE_JUMP_INSTR(offset) SINGLE_OPERAND_INSTR(RELATIVE_JUMP, ADDRESS_OFFSET(RELATIVE_JUMP, offset))
#define JUMP_TRUE_INSTR(offset) PUSH_INSTR(1), SINGLE_OPERAND_INSTR(JUMP_TRUE, ADDRESS_OFFSET(JUMP_TRUE, offset))
#define JUMP_FALSE_INSTR(offset) PUSH_INSTR(0), SINGLE_OPERAND_INSTR(JUMP_FALSE, ADDRESS_OFFSET(JUMP_FALSE, offset))
// JUMP_TABLE needs to be manually created since it takes variable number of operands ...

#define LOAD_CARRY_BORROW_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_CARRY_BORROW_FLAG)
#define LOAD_MOST_SIGNIFICANT_BIT_INSTR() NO_OPERAND_INSTR(LOAD_MOST_SIGNIFICANT_BIT_FLAG)
#define LOAD_ZERO_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_ZERO_FLAG)

INLINE_FUNC_SIGNATURE(evaluate);

#define WORD_SIZE 1

#define re_interpret(value, from_type, to_type)  (((union {to_type to_value; from_type from_value;})(value)).to_value)
#define word_as_float(word) re_interpret(word, word_type, float_type)
#define float_as_word(double_value) re_interpret(double_value, float_type, word_type)
#define double_as_signed_word(double_value) re_interpret(double_value, double, signed_word_type)


//inline void push_word(word_type word, cpu_type *cpu, virtual_memory_type *mem, struct kernel_type *os)
//{
//    set_word(mem, stack_pointer(cpu), word);
//    set_stack_pointer(cpu, (stack_pointer(cpu) - WORD_SIZE));
//}
#define push_word(word, cpu, mem, os) (set_word(mem, stack_pointer(cpu), word), update_stack_pointer(cpu, -WORD_SIZE))

//inline word_type pop_word(cpu_type *cpu, virtual_memory_type *mem, struct kernel_type *os)
//{
//    set_stack_pointer(cpu, (stack_pointer(cpu) + WORD_SIZE));
//    return get_word(mem, stack_pointer(cpu));
//}
#define pop_word(cpu, mem, os) (update_stack_pointer(cpu, WORD_SIZE), get_word(mem, stack_pointer(cpu)))


#endif