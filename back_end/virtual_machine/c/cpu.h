// Instruction IDS ...

#ifndef _CPU_H_
#define _CPU_H_

#include "word_type.h"

#define EVAL0(...) __VA_ARGS__
#define EVAL1(...) EVAL0 (EVAL0 (EVAL0 (__VA_ARGS__)))
#define EVAL2(...) EVAL1 (EVAL1 (EVAL1 (__VA_ARGS__)))
#define EVAL3(...) EVAL2 (EVAL2 (EVAL2 (__VA_ARGS__)))
#define EVAL4(...) EVAL3 (EVAL3 (EVAL3 (__VA_ARGS__)))
#define EVAL(...)  EVAL4 (EVAL4 (EVAL4 (__VA_ARGS__)))

#define MAP_END(...)

#define MAP_OUT
#define MAP_GET_END() 0, MAP_END
#define MAP_NEXT0(item, next, ...) next MAP_OUT
#define MAP_NEXT1(item, next) MAP_NEXT0 (item, next, 0)
#define MAP_NEXT(item, next)  MAP_NEXT1 (MAP_GET_END item, next)

#define MAP0(f, x, peek, ...) f(x) MAP_NEXT (peek, MAP1) (f, peek, __VA_ARGS__)
#define MAP1(f, x, peek, ...) f(x) MAP_NEXT (peek, MAP0) (f, peek, __VA_ARGS__)
#define MAP(f, ...) EVAL (MAP1 (f, __VA_ARGS__, (), 0))

#define HALT_INSTR_ID 255

#define PUSH_INSTR_ID 2
#define POP_INSTR_ID 254
#define LOAD_INSTR_ID 3
#define SET_INSTR_ID 252

#define LOAD_BASE_STACK_POINTER_INSTR_ID 7
#define SET_BASE_STACK_POINTER_INSTR_ID 249
#define LOAD_STACK_POINTER_INSTR_ID 8
#define SET_STACK_POINTER_INSTR_ID 248

#define ALLOCATE_INSTR_ID 9
#define DUP_INSTR_ID 5
#define SWAP_INSTR_ID 6

#define ADD_INSTR_ID 11
#define SUBTRACT_INSTR_ID 245

#define MULTIPLY_INSTR_ID 12
#define DIVIDE_INSTR_ID 244

#define MOD_INSTR_ID 13

#define SHIFT_LEFT_INSTR_ID 14
#define SHIFT_RIGHT_INSTR_ID 242

#define OR_INSTR_ID 15
#define AND_INSTR_ID 241
#define XOR_INSTR_ID 16
#define NOT_INSTR_ID 17

#define ADD_FLOAT_INSTR_ID 18
#define SUBTRACT_FLOAT_INSTR_ID 238
#define MULTIPLY_FLOAT_INSTR_ID 19
#define DIVIDE_FLOAT_INSTR_ID 237

#define CONVERT_TO_FLOAT_INSTR_ID 23
#define CONVERT_TO_FLOAT_FROM_UNSIGNED_INSTR_ID 24
#define CONVERT_TO_INTEGER_INSTR_ID 233

#define ABSOLUTE_JUMP_INSTR_ID 20
#define JUMP_FALSE_INSTR_ID 21
#define JUMP_TRUE_INSTR_ID 235
#define JUMP_TABLE_INSTR_ID 22
#define RELATIVE_JUMP_INSTR_ID 25

#define LOAD_ZERO_FLAG_INSTR_ID 30
#define LOAD_CARRY_BORROW_FLAG_INSTR_ID 31
#define LOAD_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID 32

#define PASS_INSTR_ID 50
#define SYSTEM_CALL_INSTR_ID 128

#define POSTFIX_UPDATE_INSTR_ID 4

#define COMPARE_INSTR_ID 10
#define COMPARE_FLOAT_INSTR_ID 243

#define LOAD_NON_ZERO_FLAG_INSTR_ID 226

#define LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG_INSTR_ID 33
#define LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID 34

#define LOAD_ZERO_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID 222
#define LOAD_ZERO_CARRY_BORROW_FLAG_INSTR_ID 223
#define LOAD_NON_CARRY_BORROW_FLAG_INSTR_ID 225
#define LOAD_NON_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID 224

#define LOAD_INSTRUCTION_POINTER_INSTR_ID 246

#define STRING(value) #value
#define INSTR_ID(instr) instr ## _INSTR_ID

#define INSTRUCTIONS    \
HALT,               \
PUSH, POP,          \
LOAD, SET,          \
LOAD_BASE_STACK_POINTER, SET_BASE_STACK_POINTER, LOAD_STACK_POINTER, SET_STACK_POINTER,         \
ALLOCATE, DUP,  SWAP,                                                                           \
ADD, SUBTRACT, MULTIPLY, DIVIDE, MOD, SHIFT_LEFT, SHIFT_RIGHT, OR, AND, XOR, NOT,               \
ADD_FLOAT, SUBTRACT_FLOAT, MULTIPLY_FLOAT, DIVIDE_FLOAT,                                        \
CONVERT_TO_FLOAT, CONVERT_TO_FLOAT_FROM_UNSIGNED, CONVERT_TO_INTEGER,                           \
ABSOLUTE_JUMP, JUMP_FALSE, JUMP_TRUE, JUMP_TABLE, RELATIVE_JUMP,                                \
LOAD_ZERO_FLAG, LOAD_CARRY_BORROW_FLAG, LOAD_MOST_SIGNIFICANT_BIT_FLAG,                         \
PASS, SYSTEM_CALL, POSTFIX_UPDATE,                                                              \
COMPARE, COMPARE_FLOAT, LOAD_NON_ZERO_FLAG, LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG,                \
LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG, LOAD_ZERO_MOST_SIGNIFICANT_BIT_FLAG,               \
LOAD_ZERO_CARRY_BORROW_FLAG, LOAD_NON_CARRY_BORROW_FLAG, LOAD_NON_MOST_SIGNIFICANT_BIT_FLAG,    \
LOAD_INSTRUCTION_POINTER

#define INSTRUCTION_NAME_ENTRY(instr) [INSTR_ID(instr)] = STRING(instr),

#define INSTRUCTION_NAMES                               \
    [0 ... 255] = "INVALID INSTRUCTION",                \
    MAP(INSTRUCTION_NAME_ENTRY, INSTRUCTIONS)

extern const char *_instr_names_[256];
#define INSTR_NAME(instr_id) (_instr_names_[instr_id])

#define get_label(instr) _ ## instr ## _ ## IMPLEMENTATION
#define INSTR_IMPLEMENTATION_ENTRY(instr) [INSTR_ID(instr)] = &&get_label(instr),
#define INSTR_IMPLEMENTATION_ADDRESS(invalid_instr_label)  \
    [0 ... 255] = &&invalid_instr_label,                   \
    MAP(INSTR_IMPLEMENTATION_ENTRY, INSTRUCTIONS)

#define evaluate_instr(offsets, instr_id) goto *offsets[instr_id]


#define INSTRUCTION_SIZE 1
#define WIDE_INSTRUCTION_SIZE (2*INSTRUCTION_SIZE)

#define INSTRUCTION_SIZES \
    [0 ... 255] = INSTRUCTION_SIZE, \
    [INSTR_ID(PUSH)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(LOAD)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(SET)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(JUMP_FALSE)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(JUMP_TRUE)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(RELATIVE_JUMP)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(ALLOCATE)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(DUP)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(SWAP)] = WIDE_INSTRUCTION_SIZE,  \
    [INSTR_ID(JUMP_TABLE)] = WIDE_INSTRUCTION_SIZE, \
    [INSTR_ID(POSTFIX_UPDATE)] = WIDE_INSTRUCTION_SIZE

extern const word_type _instr_sizes_[256];
#define INSTR_SIZE(instr_id) (_instr_sizes_[(instr_id)])


struct cpu_type {
    word_type
    // Since the stack pointer will be the most heavily accessed value better have it as the first one
        stack_pointer,
        base_pointer,
        instr_pointer,
        flags;
};
// C guarantees that the address of the first member and the struct itself are the same (no need for member calcs)
#define stack_pointer(cpu) (*(word_type *)(cpu))
#define set_stack_pointer(cpu, st_ptr) (stack_pointer(cpu) = (st_ptr))
#define update_stack_pointer(cpu, amount) (stack_pointer(cpu) += (amount))
#define base_pointer(cpu) ((cpu)->base_pointer)
#define set_base_pointer(cpu, b_ptr) (base_pointer(cpu) = (b_ptr))
#define instr_pointer(cpu) ((cpu)->instr_pointer)
#define set_instr_pointer(cpu, ptr) (instr_pointer(cpu) = (ptr))
#define update_instr_pointer(cpu, amount) (instr_pointer(cpu) += (amount))

// DO NOT CHANGE THIS ORDER!!!!!
#define NON_ZERO_FLAG_INDEX 0 // !=
#define ZERO_FLAG_INDEX 1 // ==

#define NON_CARRY_BORROW_FLAG_INDEX 2 // unsigned >=
#define CARRY_BORROW_FLAG_INDEX 3 // unsigned <
#define NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX 4 // unsigned >
#define ZERO_CARRY_BORROW_FLAG_INDEX 5 // unsigned <=

#define NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX 6 // signed >=
#define MOST_SIGNIFICANT_BIT_FLAG_INDEX 7 // signed <
#define NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX 8 // signed >
#define ZERO_MOST_SIGNIFICANT_BIT_FLAG_INDEX 9 // signed <=

#define MSB_OFFSET(_type) (BYTE_BIT_SIZE * sizeof(_type))
#define MSB_MASK(_type) ((_type)1 << (MSB_OFFSET(_type) - 1))

// There are 4 flags, each with 2 possible values (0 or 1), so 2**4 or 16 possible values
// instead of checking each lets just build a table with all the possible values and their mask

#define MASK(index) (1 << index)

#define flags(cpu) ((cpu)->flags)
#define set_flags(cpu, value) (flags(cpu) = (value))

#define flag_from_value(value, flag_index)  ((value & MASK(flag_index)) >> flag_index)
#define get_flag(cpu, flag) flag_from_value(flags(cpu), flag)

#define zero_flag(cpu) get_flag(cpu, ZERO_FLAG_INDEX)

#define non_zero_flag(cpu) get_flag(cpu, NON_ZERO_FLAG_INDEX)

#define carry_borrow_flag(cpu) get_flag(cpu, CARRY_BORROW_FLAG_INDEX)

#define most_significant_bit_flag(cpu) get_flag(cpu, MOST_SIGNIFICANT_BIT_FLAG_INDEX)

struct kernel_type;

#define FUNC_SIGNATURE(func_name) void func_name(struct cpu_type *cpu, word_type *mem, struct kernel_type *os)

#define INLINE_FUNC_SIGNATURE(func_name) INLINE FUNC_SIGNATURE(func_name)

#define NO_OPERAND_INSTR(instr) INSTR_ID(instr)
#define SINGLE_OPERAND_INSTR(instr, operand) NO_OPERAND_INSTR(instr), operand
#define PASS_INSTR() NO_OPERAND_INSTR(PASS)
#define HALT_INSTR() NO_OPERAND_INSTR(HALT)
#define PUSH_INSTR(operand) SINGLE_OPERAND_INSTR(PUSH, operand)
#define STACK_OPERAND_INSTR(operand, instr) PUSH_INSTR(operand), NO_OPERAND_INSTR(instr)

#define POP_INSTR() NO_OPERAND_INSTR(POP)

#define LOAD_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(LOAD, quantity)
#define SET_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET, quantity)

#define LOAD_BASE_STACK_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_BASE_STACK_POINTER)
#define SET_BASE_STACK_POINTER_INSTR(value) STACK_OPERAND_INSTR(value, SET_BASE_STACK_POINTER)

#define LOAD_STACK_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_STACK_POINTER)
#define SET_STACK_POINTER_INSTR(value) STACK_OPERAND_INSTR(value, SET_STACK_POINTER)

#define SWAP_INSTR(operand) SINGLE_OPERAND_INSTR(SWAP, operand)
#define DUP_INSTR(operand) SINGLE_OPERAND_INSTR(DUP, operand)

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
#define NOT_INSTR(value) STACK_OPERAND_INSTR(value, NOT)

#define COMPARE_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, COMPARE)
#define COMPARE_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, COMPARE_FLOAT)

//PUSH_INSTR(float_as_word(oper_1)), PUSH_INSTR(float_as_word(oper_2)), NO_OPERAND_INSTR(instr)
#define BINARY_FLOAT_INSTR(oper_1, oper_2, instr) BINARY_INTEGRAL_INSTR(float_as_word(oper_1), float_as_word(oper_2), instr)
#define ADD_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, ADD_FLOAT)
#define SUBTRACT_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, SUBTRACT_FLOAT)
#define MULTIPLY_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, MULTIPLY_FLOAT)
#define DIVIDE_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, DIVIDE_FLOAT)

#define CONVERT_TO_FLOAT_INSTR(oper_1) PUSH_INSTR(oper_1), NO_OPERAND_INSTR(CONVERT_TO_FLOAT)
#define CONVERT_TO_FLOAT_FROM_UNSIGNED_INSTR(oper_1) PUSH_INSTR(oper_1), NO_OPERAND_INSTR(CONVERT_TO_FLOAT_FROM_UNSIGNED)
#define CONVERT_TO_INTEGER_INSTR(oper_1) PUSH_INSTR(float_as_word(oper_1)), NO_OPERAND_INSTR(CONVERT_TO_INTEGER)

#define ABSOLUTE_JUMP_INSTR(addr) STACK_OPERAND_INSTR(addr, ABSOLUTE_JUMP)

#define ADDRESS_OFFSET(instr, offset) (offset * WORD_SIZE)
#define RELATIVE_JUMP_INSTR(offset) SINGLE_OPERAND_INSTR(RELATIVE_JUMP, ADDRESS_OFFSET(RELATIVE_JUMP, offset))
#define JUMP_TRUE_INSTR(offset) PUSH_INSTR(1), SINGLE_OPERAND_INSTR(JUMP_TRUE, ADDRESS_OFFSET(JUMP_TRUE, offset))
#define JUMP_FALSE_INSTR(offset) PUSH_INSTR(0), SINGLE_OPERAND_INSTR(JUMP_FALSE, ADDRESS_OFFSET(JUMP_FALSE, offset))
// JUMP_TABLE needs to be manually created since it takes variable number of operands ...

#define LOAD_CARRY_BORROW_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_CARRY_BORROW_FLAG)
#define UNSIGNED_LESS_THAN_INSTR LOAD_CARRY_BORROW_FLAG_INSTR

#define LOAD_NON_CARRY_BORROW_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_NON_CARRY_BORROW_FLAG)
#define UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR LOAD_NON_CARRY_BORROW_FLAG_INSTR

#define LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG)
#define UNSIGNED_GREATER_THAN_INSTR LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG_INSTR

#define LOAD_ZERO_CARRY_BORROW_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_ZERO_CARRY_BORROW_FLAG)
#define UNSIGNED_LESS_THAN_OR_EQUAL_INSTR LOAD_ZERO_CARRY_BORROW_FLAG_INSTR

#define LOAD_MOST_SIGNIFICANT_BIT_INSTR() NO_OPERAND_INSTR(LOAD_MOST_SIGNIFICANT_BIT_FLAG)
#define SIGNED_LESS_THAN_INSTR LOAD_MOST_SIGNIFICANT_BIT_INSTR

#define LOAD_NON_MOST_SIGNIFICANT_BIT_INSTR() NO_OPERAND_INSTR(LOAD_NON_MOST_SIGNIFICANT_BIT_FLAG)
#define SIGNED_GREATER_THAN_OR_EQUAL_INSTR LOAD_NON_MOST_SIGNIFICANT_BIT_INSTR

#define LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_INSTR() NO_OPERAND_INSTR(LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG)
#define SIGNED_GREATER_THAN_INSTR LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_INSTR

#define LOAD_ZERO_MOST_SIGNIFICANT_BIT_INSTR() NO_OPERAND_INSTR(LOAD_ZERO_MOST_SIGNIFICANT_BIT_FLAG)
#define SIGNED_LESS_THAN_OR_EQUAL_INSTR LOAD_ZERO_MOST_SIGNIFICANT_BIT_INSTR

#define LOAD_ZERO_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_ZERO_FLAG)
#define EQUAL_INSTR LOAD_ZERO_FLAG_INSTR

#define LOAD_NON_ZERO_FLAG_INSTR() NO_OPERAND_INSTR(LOAD_NON_ZERO_FLAG)
#define NOT_EQUAL_INSTR LOAD_NON_ZERO_FLAG_INSTR

#define LOAD_INSTRUCTION_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_INSTRUCTION_POINTER)

#define POSTFIX_UPDATE_INSTR(quantity) SINGLE_OPERAND_INSTR(POSTFIX_UPDATE, quantity)
#define ALLOCATE_INSTR(quantity) SINGLE_OPERAND_INSTR(ALLOCATE, -quantity)

INLINE_FUNC_SIGNATURE(evaluate);

#define re_interpret(value, from_type, to_type)  (((union {to_type to_value; from_type from_value;})(value)).to_value)
#define word_as_float(word) re_interpret(word, word_type, float_type)
#define float_as_word(double_value) re_interpret(double_value, float_type, word_type)
#define double_as_signed_word(double_value) re_interpret(double_value, double, signed_word_type)

#define MSB(value) (value >> (word_type)((BYTE_BIT_SIZE * sizeof(word_type)) - 1))

#endif
