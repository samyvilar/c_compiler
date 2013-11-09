#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "vm.h"
#include "cpu.h"
#include "kernel.h"

#define pop_word(cpu, mem, os) (update_stack_pointer(cpu, WORD_SIZE), *(word_type *)stack_pointer(cpu))

#define assert_equal(value_1, value_2, test_id) do {\
    word_type _value_1 = value_1, _value_2 = value_2; \
    if (_value_1 != _value_2) \
        printf("test %s failed! " WORD_PRINTF_FORMAT " != " WORD_PRINTF_FORMAT "\n", test_id, _value_1, _value_2);  \
    } while (0)

INLINE word_type *load_instrs(word_type *instrs, word_type amount, word_type *mem, struct cpu_type *cpu)
{
    memcpy((void *)instr_pointer(cpu), instrs, amount * sizeof(word_type));
    return mem;
}

#define EXECUTE(code)  evaluate(cpu, load_instrs(instrs, sizeof(instrs)/sizeof(instrs[0]), mem, cpu), os)

#define TEST_FUNC_SIGNATURE(func_name) void func_name(struct cpu_type *cpu, word_type *mem, struct kernel_type *os)

TEST_FUNC_SIGNATURE(test_push_pop)  {
    word_type instrs[] = {
            PUSH_INSTR(14123),
            HALT_INSTR()
    };

    EXECUTE(instrs);
    assert_equal(14123, pop_word(cpu, mem, os), "PUSH");
}

TEST_FUNC_SIGNATURE(test_load_set)  {
    word_type instrs[] = {
        RELATIVE_JUMP_INSTR(2),
        0,
        0,
        PUSH_INSTR(123123),  // push values ...
        PUSH_INSTR(141422),
        SET_INSTR(instr_pointer(cpu) + 2*WORD_SIZE, 2),  // copy values ...
        POP_INSTR(),
        POP_INSTR(),
        PUSH_INSTR(0), // zero out values ...
        PUSH_INSTR(0),
        LOAD_INSTR(instr_pointer(cpu) + 2*WORD_SIZE, 2), // reload values ...
        HALT_INSTR()
    };

    EXECUTE(instrs);
    assert_equal(141422, pop_word(cpu, mem, os), "test_load_set");
    assert_equal(123123, pop_word(cpu, mem, os), "test_load_set");
}

TEST_FUNC_SIGNATURE(test_load_set_registers) {
    word_type
        _base_ptr = base_pointer(cpu) - 100*WORD_SIZE,
        _stack_ptr = stack_pointer(cpu) - 1100*WORD_SIZE;
    
    word_type instrs[] = {
            SET_BASE_STACK_POINTER_INSTR(_base_ptr),
            SET_STACK_POINTER_INSTR(_stack_ptr),
            LOAD_STACK_POINTER_INSTR(),
            LOAD_BASE_STACK_POINTER_INSTR(),
            HALT_INSTR()
    };

    EXECUTE(instrs);
    assert_equal(_base_ptr, pop_word(cpu, mem, os), "test_load_set_base_stack_pointer");
    assert_equal(_stack_ptr, pop_word(cpu, mem, os), "test_load_set_stack_pointer");
}

TEST_FUNC_SIGNATURE(test_integral) {
    word_type instrs[] = {
            ADD_INSTR(123123, 13524343),
            SUBTRACT_INSTR(1249124, 235234),
            MULTIPLY_INSTR(12412452, 542645),
            DIVIDE_INSTR(12309707, 109740972),
            MOD_INSTR(1070213, 242),
            SHIFT_LEFT_INSTR(4271072, 21),
            SHIFT_RIGHT_INSTR(470927, 12),
            OR_INSTR(970237, 74927),
            AND_INSTR(429740, 47373),
            XOR_INSTR(242380, 412),
            NOT_INSTR(1232),
            HALT_INSTR()
    };

    EXECUTE(instrs);
    assert_equal(~(word_type)1232, pop_word(cpu, mem, os), "test_not");
    assert_equal((word_type)242380 ^ 412, pop_word(cpu, mem, os), "test_xor");
    assert_equal((word_type)429740 & 47373, pop_word(cpu, mem, os), "test_and");
    assert_equal((word_type)970237 | 74927, pop_word(cpu, mem, os), "test_or");
    assert_equal((word_type)470927 >> 12, pop_word(cpu, mem, os), "test_shift_right");
    assert_equal((word_type)4271072 << 21, pop_word(cpu, mem, os), "test_shift_left");
    assert_equal((word_type)1070213 % 242, pop_word(cpu, mem, os), "test_mod");
    assert_equal((word_type)12309707 / 109740972, pop_word(cpu, mem, os), "test_division");
    assert_equal((word_type)12412452 * 542645, pop_word(cpu, mem, os), "test_multiplication");
    assert_equal((word_type)1249124 - 235234, pop_word(cpu, mem, os), "test_subtraction");
    assert_equal((word_type)123123 + 13524343, pop_word(cpu, mem, os), "test_addition");
}

TEST_FUNC_SIGNATURE(test_integral_negative) {
    word_type instrs[] = {
            ADD_INSTR(-1224823, -4123232),
            SUBTRACT_INSTR(-122132, -41232),
            DIVIDE_INSTR(-1232312, -42132),
            MULTIPLY_INSTR(-121321, -5324534),
            HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(((word_type)-121321) * -5324534, pop_word(cpu, mem, os), "test_multiplication_negative");
    assert_equal(((word_type)-1232312) / -42132, pop_word(cpu, mem, os), "test_division_negative");
    assert_equal(((word_type)-122132) - -41232, pop_word(cpu, mem, os), "test_subtraction_negative");
    assert_equal(((word_type)-1224823) + -4123232, pop_word(cpu, mem, os), "test_addition_negative");
}

TEST_FUNC_SIGNATURE(test_arithmetic_floats) {
    word_type instrs[] = {
            ADD_FLOAT_INSTR((float_type)123.12423, (float_type)1482424.12322),
            SUBTRACT_FLOAT_INSTR((float_type)94124.213, (float_type)9421.4122),
            MULTIPLY_FLOAT_INSTR((float_type)123942.1232, (float_type)5314.214),
            DIVIDE_FLOAT_INSTR((float_type)131232.1234, (float_type)24123.214),
            HALT_INSTR()
    };
    EXECUTE(instrs);

    assert_equal(float_as_word((float_type)131232.1234 / (float_type)24123.214), pop_word(cpu, mem, os), "test_divide_float");
    assert_equal(float_as_word((float_type)123942.1232 * (float_type)5314.214), pop_word(cpu, mem, os), "test_multiply_float");
    assert_equal(float_as_word((float_type)94124.213 - (float_type)9421.4122), pop_word(cpu, mem, os), "test_subtract_float");
    assert_equal(float_as_word((float_type)123.12423 + (float_type)1482424.12322), pop_word(cpu, mem, os), "test_add_float");
}

TEST_FUNC_SIGNATURE(test_conversions) {
    word_type instrs[] = {
            CONVERT_TO_FLOAT_INSTR(12312323),
            CONVERT_TO_INTEGER_INSTR((float_type)1232123.1232),
            CONVERT_TO_FLOAT_FROM_UNSIGNED_INSTR((word_type)-1),
            CONVERT_TO_FLOAT_INSTR(-1),
            HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(re_interpret((float_type)-1.0, float_type, word_type), pop_word(cpu, mem, os), "test_convert_signed_to_float");
    assert_equal(float_as_word((float_type)(word_type)-1), pop_word(cpu, mem, os), "test_convert_to_float_from_unsigned");
    assert_equal((word_type)1232123, pop_word(cpu, mem, os), "test_convert_to_int");
    assert_equal(float_as_word((float_type)12312323.0), pop_word(cpu, mem, os), "test_convert_to_float");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_equality) {
    word_type instrs[] = {
        COMPARE_INSTR(-1, -1),
        EQUAL_INSTR(),                              // loads 1
        NOT_EQUAL_INSTR(),                          // loads 0
        
        SIGNED_LESS_THAN_INSTR(),                   // loads 0
        UNSIGNED_LESS_THAN_INSTR(),                 // loads 0
        SIGNED_GREATER_THAN_INSTR(),                // loads 0
        UNSIGNED_GREATER_THAN_INSTR(),              // loads 0
        
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 1
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),       // loads 1
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),     // loads 1
        
        COMPARE_INSTR(-1, 1),
        EQUAL_INSTR(),                              // loads 0
        NOT_EQUAL_INSTR(),                          // loads 1
        
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 0
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),       // loads 0
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),     // loads 1
        
        HALT_INSTR()
    };
    EXECUTE(instrs);
    
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (unsigned)(-1 >= 1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (signed)(-1 >= 1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (unsigned)(-1 <= 1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (signed)(-1 <= 1)");
    
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (-1 != 1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (-1 == 1)");
    
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (unsigned)(-1 >= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (signed)(-1 >= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (unsigned)(-1 <= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (signed)(-1 <= -1)");

    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (unsigned)(-1 > -1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (signed)(-1 > -1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (unsigned)(-1 < -1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (signed)(-1 < -1)");

    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_equality (-1 != -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_equality (-1 == -1)");
}


TEST_FUNC_SIGNATURE(test_comparison_flags_floats_equality) {
    word_type instrs[] = {
        COMPARE_FLOAT_INSTR(-1.0, -1.0),
        EQUAL_INSTR(),                              // loads 1
        NOT_EQUAL_INSTR(),                          // loads 0
        
        SIGNED_LESS_THAN_INSTR(),                   // loads 0
        UNSIGNED_LESS_THAN_INSTR(),                 // loads 0
        SIGNED_GREATER_THAN_INSTR(),                // loads 0
        UNSIGNED_GREATER_THAN_INSTR(),              // loads 0
        
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 1
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),       // loads 1
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),     // loads 1
        
        COMPARE_FLOAT_INSTR(10.0, -1.0),
        EQUAL_INSTR(),                              // loads 0
        NOT_EQUAL_INSTR(),                          // loads 1
        
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 0
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),       // loads 1

        HALT_INSTR()
    };
    EXECUTE(instrs);
    
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (signed)(10.0 >= -1.0)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (signed)(10.0 <= -1.0)");
    
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (10.0 != -1.0)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (10.0 == -1.0)");
    
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (unsigned)(-1.0 >= -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (signed)(-1.0 >= -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (unsigned)(-1.0 <= -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (signed)(-1.0 <= -1.0)");
    
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (unsigned)(-1.0 > -1.0)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (signed)(-1.0 > -1.0)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (unsigned)(-1.0 < -1.0)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (signed)(-1.0 < -1.0)");
    
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (-1.0 != -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_equality (-1.0 == -1.0)");
}


TEST_FUNC_SIGNATURE(test_comparison_flags_floats_less_than) {
    word_type instrs[] = {
        COMPARE_FLOAT_INSTR(-1.0, 10.0),
        SIGNED_LESS_THAN_INSTR(),                 // loads 1
        COMPARE_FLOAT_INSTR(10.0, -1.0),
        SIGNED_LESS_THAN_INSTR(),                 // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_less_than (10.0 < -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_less_than (-1.0 < 10)");
}


TEST_FUNC_SIGNATURE(test_comparison_flags_floats_less_than_or_equal) {
    word_type instrs[] = {
        COMPARE_FLOAT_INSTR(1.0, 1.0),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_FLOAT_INSTR(-1.0, -1.0),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_FLOAT_INSTR(-1.0, 10.0),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_FLOAT_INSTR(10.0, -1.0),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 0
        
        HALT_INSTR()
    };
    EXECUTE(instrs);
    
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_less_than_or_equal (10.0 <= -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_less_than_or_equal (-1.0 <= 10.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_less_than_or_equal (-1.0 <= -1.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_less_than_or_equal (1.0 <= 1.0)");
}



TEST_FUNC_SIGNATURE(test_comparison_flags_floats_greater_than) {
    word_type instrs[] = {
        COMPARE_FLOAT_INSTR(10.0, -1.0),
        SIGNED_GREATER_THAN_INSTR(),                 // loads 1
        COMPARE_FLOAT_INSTR(-1.0, 10.0),
        SIGNED_GREATER_THAN_INSTR(),                 // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_greater_than (-1.0 > 10.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_greater_than (10.0 > -1.0)");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_floats_greater_than_or_equal) {
    word_type instrs[] = {
        COMPARE_FLOAT_INSTR(10.0, -1.0),
        SIGNED_GREATER_THAN_INSTR(),                 // loads 1
        COMPARE_FLOAT_INSTR(-1.0, 10.0),
        SIGNED_GREATER_THAN_INSTR(),                 // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_floats_greater_than_or_equal (-1.0 > 10.0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_floats_greater_than_or_equal (10.0 > -1.0)");
}


TEST_FUNC_SIGNATURE(test_comparison_flags_signed_less_than) {
    word_type instrs[] = {
        COMPARE_INSTR(-1, 10),
        SIGNED_LESS_THAN_INSTR(),                   // loads 1
        COMPARE_INSTR(10, -1),
        SIGNED_LESS_THAN_INSTR(),                   // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_signed_less_than (10 < -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_less_than (-1 < 10)");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_unsigned_greater_than) {
    word_type instrs[] = {
        COMPARE_INSTR(-1, 10),
        UNSIGNED_GREATER_THAN_INSTR(),              // loads 1
        COMPARE_INSTR(10, -1),
        UNSIGNED_GREATER_THAN_INSTR(),              // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than (10 > -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than (-1 > 10)");

}


TEST_FUNC_SIGNATURE(test_comparison_flags_signed_greater_than) {
    word_type instrs[] = {
        COMPARE_INSTR(-1, 10),
        SIGNED_GREATER_THAN_INSTR(),                // loads 0
        COMPARE_INSTR(10, -1),
        SIGNED_GREATER_THAN_INSTR(),                // loads 1
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_greater_than (10 > -1)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_signed_greater_than (-1 > 10)");
}


TEST_FUNC_SIGNATURE(test_comparison_flags_unsigned_less_than_or_equal) {
    word_type instrs[] = {
        COMPARE_INSTR(-1, -1),
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 1
        COMPARE_INSTR((word_type)-1, ~(word_type)0),
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 1
        COMPARE_INSTR(10, -1),
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 1
        COMPARE_INSTR(-1, 10),
        UNSIGNED_LESS_THAN_OR_EQUAL_INSTR(),        // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than_or_equal (-1 <= 10)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than_or_equal (10 <= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than_or_equal (-1 <= ~0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than_or_equal (-1 <= -1)");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_signed_less_than_or_equal) {
    word_type instrs[] = {
        COMPARE_INSTR(1, 1),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR((word_type)-1, ~(word_type)0),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(-1, 10),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(10, -1),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_signed_less_than_or_equal (10 <= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_less_than_or_equal (-1 <= 10)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_less_than_or_equal (-1 <= ~0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_less_than_or_equal (1 <= 1)");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_unsigned_greater_than_or_equal) {
    word_type instrs[] = {
        COMPARE_INSTR(1, 1),
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR((word_type)-1, ~(word_type)0),
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(-1, 10),
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(10, -1),
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 0
        COMPARE_INSTR(1, 10),                            // loads 0
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than_or_equal (1 >= 10)");
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than_or_equal (10 >= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than_or_equal (-1 >= 10)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than_or_equal (-1 >= ~0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_greater_than_or_equal (1 >= 1)");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_unsigned_less_than) {
    word_type instrs[] = {
        COMPARE_INSTR(1, 1),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(-1, -1),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(-1, 10),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(10, -1),
        SIGNED_LESS_THAN_OR_EQUAL_INSTR(),          // loads 0
        
        HALT_INSTR()
    };
    EXECUTE(instrs);
    
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than (10 <= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than (-1 <= 10)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than (-1 <= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_unsigned_less_than (1 <= 1)");
}

TEST_FUNC_SIGNATURE(test_comparison_flags_signed_greater_than_or_equal) {
    word_type instrs[] = {
        COMPARE_INSTR(1, 1),
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR((word_type)-1, ~(word_type)0),
        UNSIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 1
        COMPARE_INSTR(10, -1),
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),            // loads 1
        COMPARE_INSTR(-1, 10),
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),          // loads 0
        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal(0, pop_word(cpu, mem, os), "test_comparison_flags_signed_greater_than_or_equal (-1 >= 10)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_greater_than_or_equal (10 >= -1)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_greater_than_or_equal (-1 >= ~0)");
    assert_equal(1, pop_word(cpu, mem, os), "test_comparison_flags_signed_greater_than_or_equal (1 >= 1)");
}




#define test_comparison_flags                               \
    test_comparison_flags_equality,                         \
    test_comparison_flags_signed_greater_than,              \
    test_comparison_flags_signed_greater_than_or_equal,     \
    test_comparison_flags_signed_less_than,                 \
    test_comparison_flags_signed_less_than_or_equal,        \
    test_comparison_flags_unsigned_greater_than,            \
    test_comparison_flags_unsigned_greater_than_or_equal,   \
    test_comparison_flags_unsigned_less_than,               \
    test_comparison_flags_unsigned_less_than_or_equal,      \
                                                            \
    test_comparison_flags_floats_equality,                  \
    test_comparison_flags_floats_less_than,                 \
    test_comparison_flags_floats_greater_than,              \
    test_comparison_flags_floats_less_than_or_equal,        \
    test_comparison_flags_floats_greater_than_or_equal


TEST_FUNC_SIGNATURE(test_jumps) {
    word_type instrs[] = {
            ABSOLUTE_JUMP_INSTR(instr_pointer(cpu) + 4*WORD_SIZE), // [0] = PUSH [1] = ADDR, [2] = ABSOLUTE_JUMP, [3] = HALT, [4] = ...
            HALT_INSTR(),
            PUSH_INSTR(1),
            RELATIVE_JUMP_INSTR(1), // 0 jumps to the next instruction, 1 skips next instruction
            HALT_INSTR(),
            PUSH_INSTR(2),
            JUMP_TRUE_INSTR(1),
            HALT_INSTR(),
            PUSH_INSTR(3),
            JUMP_FALSE_INSTR(1),
            HALT_INSTR(),
            PUSH_INSTR(4),
            HALT_INSTR()
    };
    EXECUTE(instrs);
    word_type expected_values[] = {4, 3, 2, 1};
    unsigned int index = 0;
    for (; index < sizeof(expected_values)/sizeof(expected_values[0]); index++)
        assert_equal(expected_values[index], pop_word(cpu, mem, os), "test_jumps");
}

// jump_table takes variable number of operands so it needs to be manually created
TEST_FUNC_SIGNATURE(test_jump_table) {
    word_type instrs[] = {
            PUSH_INSTR(14),  // [0] = PUSH, [1] = 14,
            // test successful jump ...
            SINGLE_OPERAND_INSTR(JUMP_TABLE, 9), // [2] = JUMP_TABLE [3] = default jump offset ...
            4, //  [4] = number of cases
        
            // values:
            1, 2, 14, 15,
            // offsets:
            9, 9, 10, 9,

            HALT_INSTR(),  // [13]
            PUSH_INSTR(1001), // [14], [15]
            // test default jump ...
            PUSH_INSTR(10), // [16], [17]
            SINGLE_OPERAND_INSTR(JUMP_TABLE, 6),  // [18]
            2, // [19], [20]
            5, 8, // [21], [22], ...
            8, 8, // [23], [24]
            HALT_INSTR(),  // [25]
            PUSH_INSTR(1111),  // [26], [27], ...
            HALT_INSTR() // [28]
    };
    EXECUTE(instrs);
    
    assert_equal((word_type)1111, pop_word(cpu, mem, os), "test_jump_table");
    assert_equal((word_type)1001, pop_word(cpu, mem, os), "test_jump_table");
}

TEST_FUNC_SIGNATURE(test_postfix_update) {
    word_type instrs[] = {
        PUSH_INSTR(0),
        LOAD_BASE_STACK_POINTER_INSTR(),
        POSTFIX_UPDATE_INSTR(1),
        POP_INSTR(),

        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal((word_type)1, pop_word(cpu, mem, os), "test_postfix_update");
}

TEST_FUNC_SIGNATURE(test_swap) {
    word_type instrs[] = {
        PUSH_INSTR(10),
        PUSH_INSTR(2),
        SWAP_INSTR(1),

        HALT_INSTR()
    };
    EXECUTE(instrs);
    
    assert_equal((word_type)10, pop_word(cpu, mem, os), "test_swap");
    assert_equal((word_type)2, pop_word(cpu, mem, os), "test_swap");
}

TEST_FUNC_SIGNATURE(test_dup) {

    word_type instrs[] = {
        PUSH_INSTR(5),
        PUSH_INSTR(10),
        DUP_INSTR(2),
        
        HALT_INSTR()
    };
    EXECUTE(instrs);
    
    assert_equal((word_type)10, pop_word(cpu, mem, os), "test_dup");
    assert_equal((word_type)5, pop_word(cpu, mem, os), "test_dup");
    assert_equal((word_type)10, pop_word(cpu, mem, os), "test_dup");
    assert_equal((word_type)5, pop_word(cpu, mem, os), "test_dup");
}
#undef EXECUTE

void test_cpu()
{
    // reuse the memory for each test, to save some time ...
    word_type *mem = allocate_entire_physical_address_space();

    TEST_FUNC_SIGNATURE((*tests[])) = {
            test_push_pop,
            test_load_set,
            test_load_set_registers,
            test_integral,
            test_integral_negative,
            test_conversions,
            test_arithmetic_floats,
            test_comparison_flags,
            test_jumps,
            test_jump_table,
            test_swap,
            test_dup,
            test_postfix_update
    };

    unsigned int number_of_remaining_tests = sizeof(tests)/sizeof(tests[0]);
    while (number_of_remaining_tests--)
        tests[number_of_remaining_tests](
                &(struct cpu_type){
                    .instr_pointer = (word_type)mem,
                    .stack_pointer = (word_type)(mem + VM_NUMBER_OF_ADDRESSABLE_WORDS - 1),
                    .base_pointer = (word_type)(mem + VM_NUMBER_OF_ADDRESSABLE_WORDS - 1)
                },
                mem,
                &(struct kernel_type) {}
        );
}

int main()
{
    printf("testing CPU ... \n"); test_cpu(); printf("done.\n");
    return 0;
}