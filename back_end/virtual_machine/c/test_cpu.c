#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "vm.h"
#include "cpu.h"
#include "kernel.h"

#define pop_word(cpu, mem, os) (update_stack_pointer(cpu, WORD_SIZE), *((word_type *)stack_pointer(cpu) - 1))

#define assert_equal(value_1, value_2, test_id) do {\
    word_type _value_1 = value_1, _value_2 = value_2; \
    if (_value_1 != _value_2) \
        printf("test %s failed! " WORD_PRINTF_FORMAT " != " WORD_PRINTF_FORMAT "\n", test_id, _value_1, _value_2);  \
    } while (0)

INLINE word_type *load_instrs(word_type *instrs, word_type amount, word_type *mem, struct cpu_type *cpu)
{
    memcpy((void *)instr_pointer(cpu), instrs, amount * sizeof(*instrs));
    return mem;
}

#define EXECUTE(code)  evaluate(cpu, load_instrs(instrs, sizeof(instrs)/sizeof(instrs[0]), mem, cpu), os)

#define TEST_FUNC_SIGNATURE(func_name) void func_name(struct cpu_type *cpu, word_type *mem, struct kernel_type *os)

#define get_instr(instr_name, _type_) instr_name ## _type_ ## _INSTR

#define peek_from_base(bp, offset, _type_) *((get_c_type(_type_) *)bp - offset)

#define test_push_pop_impl(_type_)                                              \
    TEST_FUNC_SIGNATURE(_test_push_pop ## _type_) {                             \
        get_c_type(_type_) value = (get_c_type(_type_))1412070970737873312LL;                              \
        word_type instrs[] = {                                                  \
            get_instr(PUSH, _type_)(value),                                    \
            get_instr(POP, _type_)(),                                          \
            HALT_INSTR()                                                        \
        };                                                                      \
        EXECUTE(instrs);                                                            \
        assert_equal(base_pointer(cpu), stack_pointer(cpu), "PUSH" #_type_);     \
        assert_equal(peek_from_base(base_pointer(cpu), 1, _type_), value, "PUSH_POP" #_type_);\
    }
MAP(test_push_pop_impl, IMPL_WORD_TYPES)
#define test_push_pop_name(_type_) ,_test_push_pop ## _type_
#define test_push_pop _test_push_pop MAP(test_push_pop_name, IMPL_WORD_TYPES)


//TEST_FUNC_SIGNATURE(test_push_pop)  {
//    word_type instrs[] = {
//            PUSH_INSTR(14123),
//            HALT_INSTR()
//    };
//
//    EXECUTE(instrs);
//    assert_equal(14123, pop_word(cpu, mem, os), "PUSH");
//}

#define test_load_set_impl(_type_)                                                  \
    TEST_FUNC_SIGNATURE(_test_load_set ## _type_)  {                                           \
        get_c_type(_type_) values[] = {               \
            (get_c_type(_type_))1231232132312312LL,                       \
            (get_c_type(_type_))1231231231234LL                          \
        };\
        word_type instrs[] = {                                                      \
            PASS_INSTR(),                                                           \
            PASS_INSTR(),                                                           \
            get_instr(PUSH, _type_)(values[0]),                                       \
            get_instr(PUSH, _type_)(values[1]),                                                     \
            get_instr(SET, _type_)((word_type)instr_pointer(cpu), 2),                            \
            get_instr(POP, _type_)(),                                                            \
            get_instr(POP, _type_)(),                                                 \
            get_instr(PUSH, _type_)(0),                                                          \
            get_instr(PUSH, _type_)(0),                                                          \
            get_instr(POP, _type_)(),                                                            \
            get_instr(POP, _type_)(),                                                       \
            get_instr(LOAD, _type_)((word_type)instr_pointer(cpu), 2),                      \
            get_instr(POP, _type_)(),                                                           \
            get_instr(POP, _type_)(),                                                       \
            HALT_INSTR()\
        };\
        EXECUTE(instrs);\
        assert_equal(base_pointer(cpu), stack_pointer(cpu), "test_load_set" #_type_);\
        assert_equal(peek_from_base(base_pointer(cpu), 1, _type_), values[0], "test_load_set" #_type_);\
        assert_equal(peek_from_base(base_pointer(cpu), 2, _type_), values[1], "test_load_set" #_type_);\
    }
MAP(test_load_set_impl, IMPL_WORD_TYPES)
#define test_load_set_name(_type_) ,_test_load_set ## _type_
#define test_load_set _test_load_set MAP(test_load_set_name, IMPL_WORD_TYPES)

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
#define cast_as(operand) ((word_type) operand),
#define cast_as_HALF(operand) ((half_word_type) operand),
#define cast_as_QUARTER(operand) ((quarter_word_type) operand),
#define cast_as_ONE_EIGHTH(operand) ((one_eighth_word_type) operand),

#define test_integral_impl(_type_)\
    TEST_FUNC_SIGNATURE(_test_integral ## _type_) {\
        get_c_type(_type_) values[] = {   \
            _MAP_(cast_as ## _type_, \
                123123, 13524343,           \
                1249124, 235234,            \
                12412452, 542645,           \
                12309707, 109740972,        \
                1070213, 242,               \
                470927, 12,                 \
                970237, 74927,              \
                429740, 47373,              \
                242380, 412,                \
                1232                        \
            )};  \
        int index = -1;\
        word_type instrs[] = {                  \
            get_instr(ADD, _type_)(values[0], values[1]),    \
            get_instr(SUBTRACT, _type_)(values[2], values[3]),\
            get_instr(MULTIPLY, _type_)(values[4], values[5]),\
            get_instr(DIVIDE, _type_)(values[6], values[7]),\
            get_instr(MOD, _type_)(values[8], values[9]),\
            get_instr(SHIFT_LEFT, _type_)(values[10], values[11]),\
            get_instr(SHIFT_RIGHT, _type_)(values[12], values[13]),\
            get_instr(OR, _type_)(values[14], values[15]),\
            get_instr(AND, _type_)(values[16], values[17]),\
            get_instr(XOR, _type_)(values[18], values[19]),\
            get_instr(NOT, _type_)(values[20]),\
            HALT_INSTR()\
        };\
        EXECUTE(instrs); index = 20;\
        assert_equal((get_c_type(_type_))(~values[index]), peek_from_base(base_pointer(cpu), 11, _type_), "test_not" #_type_);\
        assert_equal((get_c_type(_type_))(values[index - 2] ^ values[index - 1]), peek_from_base(base_pointer(cpu), 10, _type_), "test_xor"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 4] & values[index - 3]),  peek_from_base(base_pointer(cpu), 9, _type_), "test_and"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 6] | values[index - 5]),  peek_from_base(base_pointer(cpu), 8, _type_), "test_or"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 8] >> values[index - 7]), peek_from_base(base_pointer(cpu), 7, _type_), "test_shift_right"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 10] << values[index - 9]), peek_from_base(base_pointer(cpu), 6, _type_), "test_shift_left"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 12] % values[index - 11]), peek_from_base(base_pointer(cpu), 5, _type_), "test_mod"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 14] / values[index - 13]), peek_from_base(base_pointer(cpu), 4, _type_), "test_division"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 16] * values[index - 15]), peek_from_base(base_pointer(cpu), 3, _type_), "test_multiplication"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 18] - values[index - 17]), peek_from_base(base_pointer(cpu), 2, _type_), "test_subtraction"#_type_);\
        assert_equal((get_c_type(_type_))(values[index - 20] + values[index - 19]), peek_from_base(base_pointer(cpu), 1, _type_), "test_addition"#_type_);\
    }
MAP(test_integral_impl, IMPL_WORD_TYPES)
#define test_integral_name(_type_) ,_test_integral ## _type_
#define test_integral _test_integral MAP(test_integral_name, IMPL_WORD_TYPES)



//TEST_FUNC_SIGNATURE(test_integral) {
//    word_type instrs[] = {
//            ADD_INSTR(123123, 13524343),
//            SUBTRACT_INSTR(1249124, 235234),
//            MULTIPLY_INSTR(12412452, 542645),
//            DIVIDE_INSTR(12309707, 109740972),
//            MOD_INSTR(1070213, 242),
//            SHIFT_LEFT_INSTR(4271072, 21),
//            SHIFT_RIGHT_INSTR(470927, 12),
//            OR_INSTR(970237, 74927),
//            AND_INSTR(429740, 47373),
//            XOR_INSTR(242380, 412),
//            NOT_INSTR(1232),
//            HALT_INSTR()
//    };
//
//    EXECUTE(instrs);
//    assert_equal(~(word_type)1232, pop_word(cpu, mem, os), "test_not");
//    assert_equal((word_type)242380 ^ 412, pop_word(cpu, mem, os), "test_xor");
//    assert_equal((word_type)429740 & 47373, pop_word(cpu, mem, os), "test_and");
//    assert_equal((word_type)970237 | 74927, pop_word(cpu, mem, os), "test_or");
//    assert_equal((word_type)470927 >> 12, pop_word(cpu, mem, os), "test_shift_right");
//    assert_equal((word_type)4271072 << 21, pop_word(cpu, mem, os), "test_shift_left");
//    assert_equal((word_type)1070213 % 242, pop_word(cpu, mem, os), "test_mod");
//    assert_equal((word_type)12309707 / 109740972, pop_word(cpu, mem, os), "test_division");
//    assert_equal((word_type)12412452 * 542645, pop_word(cpu, mem, os), "test_multiplication");
//    assert_equal((word_type)1249124 - 235234, pop_word(cpu, mem, os), "test_subtraction");
//    assert_equal((word_type)123123 + 13524343, pop_word(cpu, mem, os), "test_addition");
//}

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
        SIGNED_GREATER_THAN_OR_EQUAL_INSTR(),             // loads 0
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
            SINGLE_OPERAND_INSTR(JUMP_TABLE, ADDRESS_OFFSET(JUMP_TABLE, 9)), // [2] = JUMP_TABLE [3] = default jump offset ...
            4, //  [4] = number of cases
        
            // values:
            1, 2, 14, 15,
            // offsets:
            ADDRESS_OFFSET(JUMP_TABLE, 9), ADDRESS_OFFSET(JUMP_TABLE, 9), ADDRESS_OFFSET(JUMP_TABLE, 10), ADDRESS_OFFSET(JUMP_TABLE, 9),

            HALT_INSTR(),  // [13]
            PUSH_INSTR(1001), // [14], [15]
            // test default jump ...
            PUSH_INSTR(10), // [16], [17]
            SINGLE_OPERAND_INSTR(JUMP_TABLE, ADDRESS_OFFSET(JUMP_TABLE, 6)),  // [18]
            2, // [19], [20]
            5, 8, // [21], [22], ...
            ADDRESS_OFFSET(JUMP_TABLE, 8), ADDRESS_OFFSET(JUMP_TABLE, 8), // [23], [24]
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
        LOAD_STACK_POINTER_INSTR(),
        POSTFIX_UPDATE_INSTR(1),

        HALT_INSTR()
    };
    EXECUTE(instrs);
    assert_equal((word_type)0, pop_word(cpu, mem, os), "test_postfix_update");
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
                    .stack_pointer = (word_type)(mem + VM_NUMBER_OF_ADDRESSABLE_WORDS),
                    .base_pointer = (word_type)(mem + VM_NUMBER_OF_ADDRESSABLE_WORDS)
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