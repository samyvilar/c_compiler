// Instruction IDS ...

#ifndef _CPU_H_
#define _CPU_H_

#include "word_type.h"

#define EVAL0(...) __VA_ARGS__
#define EVAL1(...) EVAL0 (EVAL0 (EVAL0 (__VA_ARGS__)))
#define EVAL2(...) EVAL1 (EVAL1 (EVAL1 (__VA_ARGS__)))
#define EVAL3(...) EVAL2 (EVAL2 (EVAL2 (__VA_ARGS__)))
#define EVAL4(...) EVAL3 (EVAL3 (EVAL3 (__VA_ARGS__)))
#define EVAL5(...) EVAL4 (EVAL4 (EVAL4 (__VA_ARGS__)))
#define EVAL(...)  EVAL5 (EVAL5 (EVAL5 (__VA_ARGS__)))

#define MAP_END(...)

#define MAP_OUT
#define MAP_GET_END() 0, MAP_END
#define MAP_NEXT0(item, next, ...) next MAP_OUT
#define MAP_NEXT1(item, next) MAP_NEXT0 (item, next, 0)
#define MAP_NEXT(item, next)  MAP_NEXT1 (MAP_GET_END item, next)

#define MAP0(f, x, peek, ...) f(x) MAP_NEXT (peek, MAP1) (f, peek, __VA_ARGS__)
#define MAP1(f, x, peek, ...) f(x) MAP_NEXT (peek, MAP0) (f, peek, __VA_ARGS__)
#define MAP(f, ...) EVAL (MAP1 (f, __VA_ARGS__, (), 0))


// in order to apply MAP a second time we need to re-define it since the pre-processor won't apply the same token twice ...
#define _EVAL0_(...) __VA_ARGS__
#define _EVAL1_(...) _EVAL0_ (_EVAL0_ (_EVAL0_ (__VA_ARGS__)))
#define _EVAL2_(...) _EVAL1_ (_EVAL1_ (_EVAL1_ (__VA_ARGS__)))
#define _EVAL3_(...) _EVAL2_ (_EVAL2_ (_EVAL2_ (__VA_ARGS__)))
#define _EVAL4_(...) _EVAL3_ (_EVAL3_ (_EVAL3_ (__VA_ARGS__)))
#define _EVAL_(...)  _EVAL4_ (_EVAL4_ (_EVAL4_ (__VA_ARGS__)))

#define _MAP_END_(...)

#define _MAP_OUT_
#define _MAP_GET_END_() 0, _MAP_END_
#define _MAP_NEXT0_(item, next, ...) next _MAP_OUT_
#define _MAP_NEXT1_(item, next) _MAP_NEXT0_ (item, next, 0)
#define _MAP_NEXT_(item, next)  _MAP_NEXT1_ (_MAP_GET_END_ item, next)

#define _MAP0_(f, x, peek, ...) f(x) _MAP_NEXT_ (peek, _MAP1_) (f, peek, __VA_ARGS__)
#define _MAP1_(f, x, peek, ...) f(x) _MAP_NEXT_ (peek, _MAP0_) (f, peek, __VA_ARGS__)
#define _MAP_(f, ...) _EVAL_ (_MAP1_ (f, __VA_ARGS__, (), 0))


// being that 0/1 tend to be somehwat common values lets not have any instruction use them to better test the compiler ...
#define PUSH_INSTR_ID                                               2
#define LOAD_INSTR_ID                                               3
#define POSTFIX_UPDATE_INSTR_ID                                     4
#define DUP_INSTR_ID                                                5
#define SWAP_INSTR_ID                                               6
#define LOAD_BASE_STACK_POINTER_INSTR_ID                            7
#define LOAD_STACK_POINTER_INSTR_ID                                 8
#define ALLOCATE_INSTR_ID                                           9
#define COMPARE_INSTR_ID                                            10
#define ADD_INSTR_ID                                                11
#define MULTIPLY_INSTR_ID                                           12
#define MOD_INSTR_ID                                                13
#define SHIFT_LEFT_INSTR_ID                                         14
#define OR_INSTR_ID                                                 15
#define XOR_INSTR_ID                                                16
#define NOT_INSTR_ID                                                17
#define ADD_FLOAT_INSTR_ID                                          18
#define MULTIPLY_FLOAT_INSTR_ID                                     19
#define ABSOLUTE_JUMP_INSTR_ID                                      20
#define JUMP_FALSE_INSTR_ID                                         21
#define JUMP_TABLE_INSTR_ID                                         22
#define CONVERT_TO_FLOAT_FROM_INSTR_ID                              23
#define CONVERT_TO_FLOAT_FROM_SIGNED_INSTR_ID                       24
#define RELATIVE_JUMP_INSTR_ID                                      25
#define LOAD_ZERO_FLAG_INSTR_ID                                     30
#define LOAD_CARRY_BORROW_FLAG_INSTR_ID                             31
#define LOAD_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID                     32
#define LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG_INSTR_ID                33
#define LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID        34

// Extended Instructions Set        *************************************************
#define ADD_HALF_INSTR_ID                                           35
#define ADD_QUARTER_INSTR_ID                                        36
#define ADD_ONE_EIGHTH_INSTR_ID                                     37

#define SUBTRACT_HALF_INSTR_ID                                      38
#define SUBTRACT_QUARTER_INSTR_ID                                   39
#define SUBTRACT_ONE_EIGHTH_INSTR_ID                                40

#define MULTIPLY_HALF_INSTR_ID                                      41
#define MULTIPLY_QUARTER_INSTR_ID                                   42
#define MULTIPLY_ONE_EIGHTH_INSTR_ID                                43

#define DIVIDE_HALF_INSTR_ID                                        44
#define DIVIDE_QUARTER_INSTR_ID                                     45
#define DIVIDE_ONE_EIGHTH_INSTR_ID                                  46

#define MOD_HALF_INSTR_ID                                           47
#define MOD_QUARTER_INSTR_ID                                        48
#define MOD_ONE_EIGHTH_INSTR_ID                                     49

#define CONVERT_TO_HALF_FLOAT_FROM_FLOAT_INSTR_ID                   50

#define OR_HALF_INSTR_ID                                            51
#define OR_QUARTER_INSTR_ID                                         52
#define OR_ONE_EIGHTH_INSTR_ID                                      53

#define XOR_HALF_INSTR_ID                                           54
#define XOR_QUARTER_INSTR_ID                                        55
#define XOR_ONE_EIGHTH_INSTR_ID                                     56

#define AND_HALF_INSTR_ID                                           57
#define AND_QUARTER_INSTR_ID                                        58
#define AND_ONE_EIGHTH_INSTR_ID                                     59

#define NOT_HALF_INSTR_ID                                           60
#define NOT_QUARTER_INSTR_ID                                        61
#define NOT_ONE_EIGHTH_INSTR_ID                                     62

#define PUSH_HALF_INSTR_ID                                          63
#define PUSH_QUARTER_INSTR_ID                                       64
#define PUSH_ONE_EIGHTH_INSTR_ID                                    65

#define POP_HALF_INSTR_ID                                           66
#define POP_QUARTER_INSTR_ID                                        67
#define POP_ONE_EIGHTH_INSTR_ID                                     68

#define CONVERT_TO_FLOAT_FROM_HALF_INSTR_ID                         69 // unsigned half => float
#define CONVERT_TO_FLOAT_FROM_QUARTER_INSTR_ID                      70 // unsigned quarter => float
#define CONVERT_TO_FLOAT_FROM_ONE_EIGHTH_INSTR_ID                   71 // unsigned one_eight => float
#define CONVERT_TO_FLOAT_FROM_SIGNED_HALF_INSTR_ID                  72 // signed half => float
#define CONVERT_TO_FLOAT_FROM_SIGNED_QUARTER_INSTR_ID               73 // signed quarter => float
#define CONVERT_TO_FLOAT_FROM_SIGNED_ONE_EIGHTH_INSTR_ID            74 // signed one_eight => float

#define CONVERT_TO_FROM_HALF_FLOAT_INSTR_ID                         75 // float => unsigned word

#define CONVERT_TO_HALF_FROM_FLOAT_INSTR_ID                         76 // float => unsigned half

#define CONVERT_TO_HALF_FROM_HALF_FLOAT_INSTR_ID                    77 // half float => unsigned half
#define CONVERT_TO_QUARTER_FROM_FLOAT_INSTR_ID                      78 // float => unsigned quarter
#define CONVERT_TO_QUARTER_FROM_HALF_FLOAT_INSTR_ID                 79 // half float => unsigned quarter
#define CONVERT_TO_ONE_EIGHTH_FROM_FLOAT_INSTR_ID                   80 // unsigned one_eight => float
#define CONVERT_TO_ONE_EIGHTH_FROM_HALF_FLOAT_INSTR_ID              81 // hald float => unsigned one_eighth

#define COMPARE_HALF_INSTR_ID                                       82
#define COMPARE_QUARTER_INSTR_ID                                    83
#define COMPARE_ONE_EIGHTH_INSTR_ID                                 84
#define COMPARE_FLOAT_HALF_INSTR_ID                                 85

                                                                       // unsigned      => unsigned
#define CONVERT_TO_FROM_HALF_INSTR_ID                               86 // half          => word
#define CONVERT_TO_FROM_QUARTER_INSTR_ID                            87 // quarter       => word
#define CONVERT_TO_FROM_ONE_EIGHTH_INSTR_ID                         88 // one_eighth    => word
#define CONVERT_TO_HALF_FROM_INSTR_ID                               89 // word          => half
#define CONVERT_TO_QUARTER_FROM_INSTR_ID                            90 // word          => quarter
#define CONVERT_TO_ONE_EIGHTH_FROM_INSTR_ID                         91 // word          => one_eighth
#define CONVERT_TO_QUARTER_FROM_HALF_INSTR_ID                       92 // half          => quarter
#define CONVERT_TO_ONE_EIGHTH_FROM_HALF_INSTR_ID                    93 // half          => one_eighth
#define CONVERT_TO_HALF_FROM_QUARTER_INSTR_ID                       94 // quarter       => half
#define CONVERT_TO_ONE_EIGHTH_FROM_QUARTER_INSTR_ID                 95 // quarter       => one_eighth
#define CONVERT_TO_HALF_FROM_ONE_EIGHTH_INSTR_ID                    96 // one_eight     => half
#define CONVERT_TO_QUARTER_FROM_ONE_EIGHTH_INSTR_ID                 97 // one_eighth    => quarter

#define SHIFT_LEFT_HALF_INSTR_ID                                    98
#define SHIFT_LEFT_QUARTER_INSTR_ID                                 99
#define SHIFT_LEFT_ONE_EIGHTH_INSTR_ID                              100
#define SHIFT_RIGHT_HALF_INSTR_ID                                   101
#define SHIFT_RIGHT_QUARTER_INSTR_ID                                102
#define SHIFT_RIGHT_ONE_EIGHTH_INSTR_ID                             103

#define JUMP_TRUE_HALF_INSTR_ID                                     104
#define JUMP_TRUE_QUARTER_INSTR_ID                                  105
#define JUMP_TRUE_ONE_EIGHTH_INSTR_ID                               106
#define JUMP_FALSE_HALF_INSTR_ID                                    107
#define JUMP_FALSE_QUARTER_INSTR_ID                                 108
#define JUMP_FALSE_ONE_EIGHTH_INSTR_ID                              109
#define JUMP_TABLE_HALF_INSTR_ID                                    110
#define JUMP_TABLE_QUARTER_INSTR_ID                             	111
#define JUMP_TABLE_ONE_EIGHTH_INSTR_ID                              112

#define LOAD_SINGLE_INSTR_ID                                        113
#define LOAD_SINGLE_HALF_INSTR_ID                                   114
#define LOAD_SINGLE_QUARTER_INSTR_ID                                115
#define LOAD_SINGLE_ONE_EIGHTH_INSTR_ID                             116
#define LOAD_HALF_INSTR_ID                                          117
#define LOAD_QUARTER_INSTR_ID                                       118
#define LOAD_ONE_EIGHTH_INSTR_ID                                    119

#define POSTFIX_UPDATE_HALF_INSTR_ID                                120
#define POSTFIX_UPDATE_QUARTER_INSTR_ID                             121
#define POSTFIX_UPDATE_ONE_EIGHTH_INSTR_ID                          122

#define CONVERT_TO_FLOAT_FROM_HALF_FLOAT_INSTR_ID                   123

#define DIVIDE_FLOAT_HALF_INSTR_ID                                  124
#define MULTIPLY_FLOAT_HALF_INSTR_ID                                125
#define SUBTRACT_FLOAT_HALF_INSTR_ID                                126
#define ADD_FLOAT_HALF_INSTR_ID                                     127

#define DUP_SINGLE_INSTR_ID                                         128
#define DUP_SINGLE_HALF_INSTR_ID                                    129
#define DUP_SINGLE_QUARTER_INSTR_ID                                 130
#define DUP_SINGLE_ONE_EIGHTH_INSTR_ID                              131

#define DUP_HALF_INSTR_ID                                           132
#define DUP_QUARTER_INSTR_ID                                    	133
#define DUP_ONE_EIGHTH_INSTR_ID                                     134

#define SWAP_SINGLE_INSTR_ID                                        135
#define SWAP_SINGLE_HALF_INSTR_ID                                   136
#define SWAP_SINGLE_QUARTER_INSTR_ID                            	137
#define SWAP_SINGLE_ONE_EIGHTH_INSTR_ID                             138
#define SWAP_HALF_INSTR_ID                                          139
#define SWAP_QUARTER_INSTR_ID                                   	140
#define SWAP_ONE_EIGHTH_INSTR_ID                                    141

#define SET_SINGLE_INSTR_ID                                         142
#define SET_SINGLE_HALF_INSTR_ID                                    143
#define SET_SINGLE_QUARTER_INSTR_ID                             	144
#define SET_SINGLE_ONE_EIGHTH_INSTR_ID                              145
#define SET_HALF_INSTR_ID                                           146
#define SET_QUARTER_INSTR_ID                                        147
#define SET_ONE_EIGHTH_INSTR_ID                                     148

#define CONVERT_TO_HALF_FLOAT_FROM_INSTR_ID                         149 // unsigned word => half float
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_ONE_EIGHTH_INSTR_ID       150 // signed one_eight => half float
#define CONVERT_TO_HALF_FLOAT_FROM_ONE_EIGHTH_INSTR_ID              151 // unsigned one_eighth => half float
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_HALF_INSTR_ID             152 // signed half => half float
#define CONVERT_TO_HALF_FLOAT_FROM_HALF_INSTR_ID                    153 // unsigned half => half float
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_QUARTER_INSTR_ID          154 // signed quarter => half float
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_INSTR_ID                  155 // signed word => half float
#define CONVERT_TO_HALF_FLOAT_FROM_QUARTER_INSTR_ID                 156 // unsigned quarter => half float


                                                                        // signed               => signed
#define CONVERT_TO_SIGNED_FROM_SIGNED_HALF_INSTR_ID                 157 // signed half          => signed word
#define CONVERT_TO_SIGNED_FROM_SIGNED_QUARTER_INSTR_ID              158 // signed quarter       => signed word
#define CONVERT_TO_SIGNED_FROM_SIGNED_ONE_EIGHTH_INSTR_ID           159 // signed one_eighth    => signed word
#define CONVERT_TO_SIGNED_HALF_FROM_SIGNED_INSTR_ID                 160 // signed word          => signed half
#define CONVERT_TO_SIGNED_QUARTER_FROM_SIGNED_INSTR_ID              161 // signed word          => signed quarter
#define CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_SIGNED_INSTR_ID           162 // signed word          => signed one_eighth
#define CONVERT_TO_SIGNED_QUARTER_FROM_SIGNED_HALF_INSTR_ID         163 // signed half          => signed quarter
#define CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_SIGNED_HALF_INSTR_ID      164 // signed half          => signed one_eighth
#define CONVERT_TO_SIGNED_HALF_FROM_SIGNED_QUARTER_INSTR_ID         165 // signed quarter       => signed half
#define CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_SIGNED_QUARTER_INSTR_ID   166 // signed quarter       => signed one_eighth
#define CONVERT_TO_SIGNED_HALF_FROM_SIGNED_ONE_EIGHTH_INSTR_ID      167 // signed one_eight     => signed half
#define CONVERT_TO_SIGNED_QUARTER_FROM_SIGNED_ONE_EIGHTH_INSTR_ID   168 // signed one_eighth    => signed quarter


                                                                        // signed               => unsigned
#define CONVERT_TO_FROM_SIGNED_HALF_INSTR_ID                        169 // signed half          => word
#define CONVERT_TO_FROM_SIGNED_QUARTER_INSTR_ID                     170 // signed quarter       => word
#define CONVERT_TO_FROM_SIGNED_ONE_EIGHTH_INSTR_ID                  171 // signed one_eighth    => word
#define CONVERT_TO_HALF_FROM_SIGNED_INSTR_ID                        172 // signed word          => half
#define CONVERT_TO_QUARTER_FROM_SIGNED_INSTR_ID                     173 // signed word          => quarter
#define CONVERT_TO_ONE_EIGHTH_FROM_SIGNED_INSTR_ID                  174 // signed word          => one_eighth
#define CONVERT_TO_QUARTER_FROM_SIGNED_HALF_INSTR_ID                175 // signed half          => quarter
#define CONVERT_TO_ONE_EIGHTH_FROM_SIGNED_HALF_INSTR_ID             176 // signed half          => one_eighth
#define CONVERT_TO_HALF_FROM_SIGNED_QUARTER_INSTR_ID                177 // signed quarter       => half
#define CONVERT_TO_ONE_EIGHTH_FROM_SIGNED_QUARTER_INSTR_ID          178 // signed quarter       => one_eighth
#define CONVERT_TO_HALF_FROM_SIGNED_ONE_EIGHTH_INSTR_ID             179 // signed one_eight     => half
#define CONVERT_TO_QUARTER_FROM_SIGNED_ONE_EIGHTH_INSTR_ID          180 // signed one_eighth    => quarter


                                                                        // unsigned      => signed
#define CONVERT_TO_SIGNED_FROM_HALF_INSTR_ID                        181 // half          => signed word
#define CONVERT_TO_SIGNED_FROM_QUARTER_INSTR_ID                     182 // quarter       => signed word
#define CONVERT_TO_SIGNED_FROM_ONE_EIGHTH_INSTR_ID                  183 // one_eighth    => signed word
#define CONVERT_TO_SIGNED_HALF_FROM_INSTR_ID                        184 // word          => signed half
#define CONVERT_TO_SIGNED_QUARTER_FROM_INSTR_ID                     185 // word          => signed quarter
#define CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_INSTR_ID                  186 // word          => signed one_eighth
#define CONVERT_TO_SIGNED_QUARTER_FROM_HALF_INSTR_ID                187 // half          => signed quarter
#define CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_HALF_INSTR_ID             188 // half          => signed one_eighth
#define CONVERT_TO_SIGNED_HALF_FROM_QUARTER_INSTR_ID                189 // quarter       => signed half
#define CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_QUARTER_INSTR_ID          190 // quarter       => signed one_eighth
#define CONVERT_TO_SIGNED_HALF_FROM_ONE_EIGHTH_INSTR_ID             191 // one_eight     => signed half
#define CONVERT_TO_SIGNED_QUARTER_FROM_ONE_EIGHTH_INSTR_ID          192 // one_eighth    => signed quarter



// ******************************************************************************************************

#define PASS_INSTR_ID                                               220
#define SYSTEM_CALL_INSTR_ID                                        221
#define LOAD_ZERO_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID                222
#define LOAD_ZERO_CARRY_BORROW_FLAG_INSTR_ID                        223
#define LOAD_NON_MOST_SIGNIFICANT_BIT_FLAG_INSTR_ID                 224
#define LOAD_NON_CARRY_BORROW_FLAG_INSTR_ID                         225
#define LOAD_NON_ZERO_FLAG_INSTR_ID                                 226

#define CONVERT_TO_FROM_FLOAT_INSTR_ID                              233

#define JUMP_TRUE_INSTR_ID                                          235

#define DIVIDE_FLOAT_INSTR_ID                                       237
#define SUBTRACT_FLOAT_INSTR_ID                                     238
#define AND_INSTR_ID                                                241
#define SHIFT_RIGHT_INSTR_ID                                        242
#define COMPARE_FLOAT_INSTR_ID                                      243
#define DIVIDE_INSTR_ID                                             244
#define SUBTRACT_INSTR_ID                                           245
#define LOAD_INSTRUCTION_POINTER_INSTR_ID                           246
#define SET_STACK_POINTER_INSTR_ID                                  248
#define SET_BASE_STACK_POINTER_INSTR_ID                             249
#define SET_INSTR_ID                                                252
#define POP_INSTR_ID                                                254
#define HALT_INSTR_ID                                               255


#define STRING(value) #value
#define INSTR_ID(instr) instr ## _INSTR_ID

// Second generation instruction set for supporting half, quarter, one_eighth words (among other things)...
#define EXTENDED_INSTRUCTIONS \
    ADD_HALF, ADD_QUARTER, ADD_ONE_EIGHTH, SUBTRACT_HALF, SUBTRACT_QUARTER, SUBTRACT_ONE_EIGHTH,     \
    MULTIPLY_HALF, MULTIPLY_QUARTER, MULTIPLY_ONE_EIGHTH, DIVIDE_HALF, DIVIDE_QUARTER, DIVIDE_ONE_EIGHTH,    \
    MOD_HALF, MOD_QUARTER, MOD_ONE_EIGHTH, OR_HALF, OR_QUARTER, OR_ONE_EIGHTH, XOR_HALF, XOR_QUARTER, XOR_ONE_EIGHTH,    \
    AND_HALF, AND_QUARTER, AND_ONE_EIGHTH, NOT_HALF, NOT_QUARTER, NOT_ONE_EIGHTH, PUSH_HALF, PUSH_QUARTER, PUSH_ONE_EIGHTH,  \
    POP_HALF, POP_QUARTER, POP_ONE_EIGHTH, CONVERT_TO_FLOAT_FROM_HALF, CONVERT_TO_FLOAT_FROM_QUARTER, CONVERT_TO_FLOAT_FROM_ONE_EIGHTH, \
    CONVERT_TO_FLOAT_FROM_SIGNED_HALF, CONVERT_TO_FLOAT_FROM_SIGNED_QUARTER, CONVERT_TO_FLOAT_FROM_SIGNED_ONE_EIGHTH, \
    CONVERT_TO_FROM_HALF_FLOAT, CONVERT_TO_HALF_FROM_FLOAT, CONVERT_TO_HALF_FROM_HALF_FLOAT, CONVERT_TO_QUARTER_FROM_FLOAT, CONVERT_TO_QUARTER_FROM_HALF_FLOAT, \
    CONVERT_TO_ONE_EIGHTH_FROM_FLOAT, CONVERT_TO_ONE_EIGHTH_FROM_HALF_FLOAT, COMPARE_HALF, COMPARE_QUARTER, COMPARE_ONE_EIGHTH, COMPARE_FLOAT_HALF, ADD_FLOAT_HALF, \
    DIVIDE_FLOAT_HALF, MULTIPLY_FLOAT_HALF, SUBTRACT_FLOAT_HALF, SHIFT_LEFT_HALF, SHIFT_LEFT_QUARTER, SHIFT_LEFT_ONE_EIGHTH, SHIFT_RIGHT_HALF,  \
    CONVERT_TO_FROM_HALF, CONVERT_TO_FROM_QUARTER, CONVERT_TO_FROM_ONE_EIGHTH, CONVERT_TO_HALF_FROM, CONVERT_TO_QUARTER_FROM, CONVERT_TO_ONE_EIGHTH_FROM, \
    CONVERT_TO_QUARTER_FROM_HALF, CONVERT_TO_ONE_EIGHTH_FROM_HALF, CONVERT_TO_HALF_FROM_QUARTER, CONVERT_TO_ONE_EIGHTH_FROM_QUARTER, \
    CONVERT_TO_HALF_FROM_ONE_EIGHTH, CONVERT_TO_QUARTER_FROM_ONE_EIGHTH, SHIFT_RIGHT_QUARTER, SHIFT_RIGHT_ONE_EIGHTH, JUMP_TRUE_HALF, JUMP_TRUE_QUARTER, \
    JUMP_TRUE_ONE_EIGHTH, JUMP_FALSE_HALF, JUMP_FALSE_QUARTER, JUMP_FALSE_ONE_EIGHTH, JUMP_TABLE_HALF, JUMP_TABLE_QUARTER, JUMP_TABLE_ONE_EIGHTH, \
    LOAD_SINGLE ,LOAD_SINGLE_HALF ,LOAD_SINGLE_QUARTER, LOAD_SINGLE_ONE_EIGHTH ,LOAD_HALF ,LOAD_QUARTER, \
    LOAD_ONE_EIGHTH, POSTFIX_UPDATE_HALF, POSTFIX_UPDATE_QUARTER, POSTFIX_UPDATE_ONE_EIGHTH,DUP_SINGLE, \
    DUP_SINGLE_HALF, DUP_SINGLE_QUARTER, DUP_SINGLE_ONE_EIGHTH, DUP_HALF, DUP_QUARTER, DUP_ONE_EIGHTH, \
    SWAP_SINGLE ,SWAP_SINGLE_HALF, SWAP_SINGLE_QUARTER, SWAP_SINGLE_ONE_EIGHTH, SWAP_HALF, SWAP_QUARTER, \
    SWAP_ONE_EIGHTH, SET_SINGLE, SET_SINGLE_HALF, SET_SINGLE_QUARTER, SET_SINGLE_ONE_EIGHTH, SET_HALF, \
    SET_QUARTER, SET_ONE_EIGHTH, CONVERT_TO_FLOAT_FROM_HALF_FLOAT, CONVERT_TO_HALF_FLOAT_FROM_FLOAT, CONVERT_TO_HALF_FLOAT_FROM, \
    CONVERT_TO_HALF_FLOAT_FROM_SIGNED_ONE_EIGHTH, CONVERT_TO_HALF_FLOAT_FROM_ONE_EIGHTH, CONVERT_TO_HALF_FLOAT_FROM_SIGNED_HALF, \
    CONVERT_TO_HALF_FLOAT_FROM_HALF, CONVERT_TO_HALF_FLOAT_FROM_SIGNED_QUARTER, CONVERT_TO_HALF_FLOAT_FROM_SIGNED, CONVERT_TO_HALF_FLOAT_FROM_QUARTER, \
    CONVERT_TO_SIGNED_FROM_SIGNED_HALF, CONVERT_TO_SIGNED_FROM_SIGNED_QUARTER, CONVERT_TO_SIGNED_FROM_SIGNED_ONE_EIGHTH, CONVERT_TO_SIGNED_HALF_FROM_SIGNED, \
    CONVERT_TO_SIGNED_QUARTER_FROM_SIGNED, CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_SIGNED, CONVERT_TO_SIGNED_QUARTER_FROM_SIGNED_HALF, CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_SIGNED_HALF, \
    CONVERT_TO_SIGNED_HALF_FROM_SIGNED_QUARTER, CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_SIGNED_QUARTER, CONVERT_TO_SIGNED_HALF_FROM_SIGNED_ONE_EIGHTH, \
    CONVERT_TO_SIGNED_QUARTER_FROM_SIGNED_ONE_EIGHTH, CONVERT_TO_FROM_SIGNED_HALF, CONVERT_TO_FROM_SIGNED_QUARTER, CONVERT_TO_FROM_SIGNED_ONE_EIGHTH,\
    CONVERT_TO_HALF_FROM_SIGNED, CONVERT_TO_QUARTER_FROM_SIGNED, CONVERT_TO_ONE_EIGHTH_FROM_SIGNED, CONVERT_TO_QUARTER_FROM_SIGNED_HALF, \
    CONVERT_TO_ONE_EIGHTH_FROM_SIGNED_HALF, CONVERT_TO_HALF_FROM_SIGNED_QUARTER, CONVERT_TO_ONE_EIGHTH_FROM_SIGNED_QUARTER, CONVERT_TO_HALF_FROM_SIGNED_ONE_EIGHTH, \
    CONVERT_TO_QUARTER_FROM_SIGNED_ONE_EIGHTH, CONVERT_TO_SIGNED_FROM_HALF, CONVERT_TO_SIGNED_FROM_QUARTER, CONVERT_TO_SIGNED_FROM_ONE_EIGHTH, \
    CONVERT_TO_SIGNED_HALF_FROM, CONVERT_TO_SIGNED_QUARTER_FROM, CONVERT_TO_SIGNED_ONE_EIGHTH_FROM, CONVERT_TO_SIGNED_QUARTER_FROM_HALF,\
    CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_HALF, CONVERT_TO_SIGNED_HALF_FROM_QUARTER, CONVERT_TO_SIGNED_ONE_EIGHTH_FROM_QUARTER, CONVERT_TO_SIGNED_HALF_FROM_ONE_EIGHTH,\
    CONVERT_TO_SIGNED_QUARTER_FROM_ONE_EIGHTH



#define INSTRUCTIONS    \
    HALT,               \
    PUSH, POP,          \
    LOAD, SET,          \
    LOAD_BASE_STACK_POINTER, SET_BASE_STACK_POINTER, LOAD_STACK_POINTER, SET_STACK_POINTER,         \
    ALLOCATE, DUP,  SWAP,                                                                           \
    ADD, SUBTRACT, MULTIPLY, DIVIDE, MOD, SHIFT_LEFT, SHIFT_RIGHT, OR, AND, XOR, NOT,               \
    ADD_FLOAT, SUBTRACT_FLOAT, MULTIPLY_FLOAT, DIVIDE_FLOAT,                                        \
    CONVERT_TO_FLOAT_FROM, CONVERT_TO_FLOAT_FROM_SIGNED, CONVERT_TO_FROM_FLOAT,                     \
    ABSOLUTE_JUMP, JUMP_FALSE, JUMP_TRUE, JUMP_TABLE, RELATIVE_JUMP,                                \
    LOAD_ZERO_FLAG, LOAD_CARRY_BORROW_FLAG, LOAD_MOST_SIGNIFICANT_BIT_FLAG,                         \
    PASS, SYSTEM_CALL, POSTFIX_UPDATE,                                                              \
    COMPARE, COMPARE_FLOAT, LOAD_NON_ZERO_FLAG, LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG,                \
    LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG, LOAD_ZERO_MOST_SIGNIFICANT_BIT_FLAG,               \
    LOAD_ZERO_CARRY_BORROW_FLAG, LOAD_NON_CARRY_BORROW_FLAG, LOAD_NON_MOST_SIGNIFICANT_BIT_FLAG,    \
    LOAD_INSTRUCTION_POINTER, EXTENDED_INSTRUCTIONS

#define _OR_(value) value |
#define get_instr_id(instr) ,INSTR_ID(instr)
// if the max intrusction id is less than 255 (max unsigned char, then use unsigned char type to load instructions)

#if ((0 MAP(_OR_, MAP(get_instr_id, INSTRUCTIONS)) 0) <= 255)
    #define MAX_POSSIBLE_INSTRUCTION_ID 255
    #define instr_value_type unsigned char
#else
    #define MAX_POSSIBLE_INSTRUCTION_ID 512
    #define instr_value_type unsigned short
#endif

#define INSTRUCTION_NAME_ENTRY(instr) [INSTR_ID(instr)] = STRING(instr),

#define INSTRUCTION_NAMES                               \
    [0 ... MAX_POSSIBLE_INSTRUCTION_ID] = "INVALID INSTRUCTION",                \
    MAP(INSTRUCTION_NAME_ENTRY, INSTRUCTIONS)

extern const char *_instr_names_[256];
#define INSTR_NAME(instr_id) (_instr_names_[instr_id])

#define get_label(instr) _ ## instr ## _ ## IMPLEMENTATION
#define INSTR_IMPLEMENTATION_ENTRY(instr) [INSTR_ID(instr)] = &&get_label(instr),
#define INSTR_IMPLEMENTATION_ADDRESS(invalid_instr_label)  \
    [0 ... MAX_POSSIBLE_INSTRUCTION_ID] = &&invalid_instr_label,                   \
    MAP(INSTR_IMPLEMENTATION_ENTRY, INSTRUCTIONS)

#define evaluate_instr(offsets, instr_id) goto *offsets[instr_id]


#define INSTRUCTION_SIZE 1
#define WIDE_INSTRUCTION_SIZE (2*INSTRUCTION_SIZE)

// TODO: add new extended instruction set ...
#define WIDE_INSTRUCTIONS PUSH, LOAD, SET, JUMP_FALSE, JUMP_TRUE, RELATIVE_JUMP, ALLOCATE, DUP, SWAP, JUMP_TABLE, POSTFIX_UPDATE
#define INSTRUCTION_SIZES \
    [0 ... MAX_POSSIBLE_INSTRUCTION_ID] = INSTRUCTION_SIZE, \
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

extern const word_type _instr_sizes_[MAX_POSSIBLE_INSTRUCTION_ID + 1];
#define INSTR_SIZE(instr_id) (_instr_sizes_[(instr_id)])


struct cpu_type {
    word_type
        // Since the stack pointer will be the most heavily accessed value better have it as the first one ...
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
#define _MSB_MASK_(_type) ((_type)1 << (MSB_OFFSET(_type) - 1))
#define MSB_MASK() _MSB_MASK_(word_type)
#define MSB_MASK_HALF() _MSB_MASK_(half_word_type)
#define MSB_MASK_QUARTER() _MSB_MASK_(quarter_word_type)
#define MSB_MASK_ONE_EIGHTH() _MSB_MASK_(one_eighth_word_type)

#define BIT(index) ((word_type)1 << index)
#define _BIT_(index) BIT(index) |
#define MASK(value...) (MAP(_BIT_, value) 0)

#define flags(cpu) ((cpu)->flags)
#define set_flags(cpu, value) (flags(cpu) = (value))

#define flag_from_value(value, flag_index)  ((value & BIT(flag_index)) >> flag_index)
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

#define PUSH_HALF_INSTR(operand) SINGLE_OPERAND_INSTR(PUSH_HALF, operand)
#define PUSH_QUARTER_INSTR(operand) SINGLE_OPERAND_INSTR(PUSH_QUARTER, operand)
#define PUSH_ONE_EIGHTH_INSTR(operand) SINGLE_OPERAND_INSTR(PUSH_ONE_EIGHTH, operand)

#define _STACK_OPERAND_INSTR_(operand, instr, _type_) PUSH ## _type_ ## _INSTR(operand), NO_OPERAND_INSTR(instr)
#define STACK_OPERAND_INSTR(operand, instr) _STACK_OPERAND_INSTR_(operand, instr,)
#define STACK_OPERAND_HALF_INSTR(operand, instr) _STACK_OPERAND_INSTR_(operand, instr, _HALF)
#define STACK_OPERAND_QUARTER_INSTR(operand, instr) _STACK_OPERAND_INSTR_(operand, instr, _QUARTER)
#define STACK_OPERAND_ONE_EIGHTH_INSTR(operand, instr) _STACK_OPERAND_INSTR_(operand, instr, _ONE_EIGHTH)

#define POP_INSTR() NO_OPERAND_INSTR(POP)
#define POP_HALF_INSTR() NO_OPERAND_INSTR(POP_HALF)
#define POP_QUARTER_INSTR() NO_OPERAND_INSTR(POP_QUARTER)
#define POP_ONE_EIGHTH_INSTR() NO_OPERAND_INSTR(POP_ONE_EIGHTH)

#define LOAD_SINGLE_INSTR(addr) PUSH_INSTR(addr), NO_OPERAND_INSTR(LOAD_SINGLE)
#define LOAD_SINGLE_HALF_INSTR(addr) PUSH_INSTR(addr), NO_OPERAND_INSTR(LOAD_SINGLE_HALF)
#define LOAD_SINGLE_QUARTER_INSTR(addr) PUSH_INSTR(addr), NO_OPERAND_INSTR(LOAD_SINGLE_QUARTER)
#define LOAD_SINGLE_ONE_EIGHTH_INSTR(addr) PUSH_INSTR(addr), NO_OPERAND_INSTR(LOAD_SINGLE_ONE_EIGHTH)

#define LOAD_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(LOAD, quantity)
#define LOAD_HALF_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(LOAD_HALF, quantity)
#define LOAD_QUARTER_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(LOAD_QUARTER, quantity)
#define LOAD_ONE_EIGHTH_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(LOAD_ONE_EIGHTH, quantity)

#define SET_SINGLE_INSTR(addr) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_SINGLE, quantity)
#define SET_SINGLE_HALF_INSTR(addr) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_SINGLE_HALF, quantity)
#define SET_SINGLE_QUARTER_INSTR(addr) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_SINGLE_QUARTER, quantity)
#define SET_SINGLE_ONE_EIGHTH_INSTR(addr) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_SINGLE_ONE_EIGHTH, quantity)

#define SET_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET, quantity)

#define SET_HALF_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_HALF, quantity)
#define SET_QUARTER_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_QUARTER, quantity)
#define SET_ONE_EIGHTH_INSTR(addr, quantity) PUSH_INSTR(addr), SINGLE_OPERAND_INSTR(SET_ONE_EIGHTH, quantity)

#define LOAD_BASE_STACK_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_BASE_STACK_POINTER)
#define SET_BASE_STACK_POINTER_INSTR(value) STACK_OPERAND_INSTR(value, SET_BASE_STACK_POINTER)

#define LOAD_STACK_POINTER_INSTR() NO_OPERAND_INSTR(LOAD_STACK_POINTER)
#define SET_STACK_POINTER_INSTR(value) STACK_OPERAND_INSTR(value, SET_STACK_POINTER)

#define SWAP_SINGLE_INSTR NO_OPERAND_INSTR(SWAP_SINGLE_INSTR)
#define SWAP_SINGLE_HALF_INSTR NO_OPERAND_INSTR(SWAP_SINGLE_HALF)
#define SWAP_SINGLE_QUARTER_INSTR NO_OPERAND_INSTR(SWAP_SINGLE_QUARTER)
#define SWAP_SINGLE_ONE_EIGHTH_INSTR NO_OPERAND_INSTR(SWAP_SINGLE_ONE_EIGHTH)

#define SWAP_INSTR(operand) SINGLE_OPERAND_INSTR(SWAP, operand)

#define SWAP_HALF_INSTR(operand) SINGLE_OPERAND_INSTR(SWAP_HALF, operand)
#define SWAP_QUARTER_INSTR(operand) SINGLE_OPERAND_INSTR(SWAP_QUARTER, operand)
#define SWAP_ONE_EIGHTH_INSTR(operand) SINGLE_OPERAND_INSTR(SWAP_ONE_EIGHTH, operand)

#define DUP_SINGLE_INSTR NO_OPERAND_INSTR(DUP_SINGLE)
#define DUP_SINGLE_HALF_INSTR NO_OPERAND_INSTR(DUP_SINGLE_HALF)
#define DUP_SINGLE_QUARTER_INSTR NO_OPERAND_INSTR(DUP_SINGLE_QUARTER)
#define DUP_SINGLE_ONE_EIGHTH_INSTR NO_OPERAND_INSTR(DUP_SINGLE_ONE_EIGHTH)

#define DUP_INSTR(operand) SINGLE_OPERAND_INSTR(DUP, operand)

#define DUP_HALF_INSTR(operand) SINGLE_OPERAND_INSTR(DUP_HALF, operand)
#define DUP_QUARTER_INSTR(operand) SINGLE_OPERAND_INSTR(DUP_QUARTER, operand)
#define DUP_ONE_EIGHTH_INSTR(operand) SINGLE_OPERAND_INSTR(DUP_ONE_EIGHTH, operand)

#define BINARY_INTEGRAL_INSTR(oper_1, oper_2, instr) PUSH_INSTR(oper_1), PUSH_INSTR(oper_2), NO_OPERAND_INSTR(instr)
#define BINARY_INTEGRAL_HALF_INSTR(oper_1, oper_2, instr) PUSH_HALF_INSTR(oper_1), PUSH_HALF_INSTR(oper_2), NO_OPERAND_INSTR(instr)
#define BINARY_INTEGRAL_QUARTER_INSTR(oper_1, oper_2, instr) PUSH_QUARTER_INSTR(oper_1), PUSH_QUARTER_INSTR(oper_2), NO_OPERAND_INSTR(instr)
#define BINARY_INTEGRAL_ONE_EIGHTH_INSTR(oper_1, oper_2, instr) PUSH_ONE_EIGHTH_INSTR(oper_1), PUSH_ONE_EIGHTH_INSTR(oper_2), NO_OPERAND_INSTR(instr)

#define _INTEGRAL_OPERATION_(oper_1, oper_2, oper, _type_) BINARY_INTEGRAL ## _type_ ## _INSTR(oper_1, oper_2, oper ## _type_)
#define ADD_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, ADD,)
#define ADD_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, ADD, _HALF)
#define ADD_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, ADD, _QUARTER)
#define ADD_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, ADD, _ONE_EIGHTH)

#define SUBTRACT_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SUBTRACT,) 
#define SUBTRACT_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SUBTRACT, _HALF)
#define SUBTRACT_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SUBTRACT, _QUARTER)
#define SUBTRACT_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SUBTRACT, _ONE_EIGHTH)

#define MULTIPLY_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MULTIPLY,) 
#define MULTIPLY_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MULTIPLY, _HALF)
#define MULTIPLY_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MULTIPLY, _QUARTER)
#define MULTIPLY_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MULTIPLY, _ONE_EIGHTH)

#define DIVIDE_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, DIVIDE,) 
#define DIVIDE_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, DIVIDE, _HALF)
#define DIVIDE_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, DIVIDE, _QUARTER)
#define DIVIDE_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, DIVIDE, _ONE_EIGHTH)

#define MOD_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MOD,) 
#define MOD_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MOD, _HALF)
#define MOD_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MOD, _QUARTER)
#define MOD_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, MOD, _ONE_EIGHTH)

#define SHIFT_LEFT_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_LEFT,)
#define SHIFT_LEFT_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_LEFT, _HALF)
#define SHIFT_LEFT_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_LEFT, _QUARTER)
#define SHIFT_LEFT_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_LEFT, _ONE_EIGHTH)

#define SHIFT_RIGHT_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_RIGHT,)
#define SHIFT_RIGHT_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_RIGHT, _HALF)
#define SHIFT_RIGHT_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_RIGHT, _QUARTER)
#define SHIFT_RIGHT_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, SHIFT_RIGHT, _ONE_EIGHTH)

#define OR_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, OR,)
#define OR_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, OR, _HALF)
#define OR_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, OR, _QUARTER)
#define OR_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, OR, _ONE_EIGHTH)

#define AND_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, AND, )
#define AND_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, AND, _HALF)
#define AND_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, AND, _QUARTER)
#define AND_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, AND, _ONE_EIGHTH)

#define XOR_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, XOR, )
#define XOR_HALF_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, XOR, _HALF)
#define XOR_QUARTER_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, XOR, _QUARTER)
#define XOR_ONE_EIGHTH_INSTR(oper_1, oper_2) _INTEGRAL_OPERATION_(oper_1, oper_2, XOR, _ONE_EIGHTH)

#define _NOT_INSTR_(value, _type_) STACK_OPERAND ## _type_ ## _INSTR(value, NOT ## _type_)
#define NOT_INSTR(value) _NOT_INSTR_(value, )
#define NOT_HALF_INSTR(value) _NOT_INSTR_(value, _HALF)
#define NOT_QUARTER_INSTR(value) _NOT_INSTR_(value, _QUARTER)
#define NOT_ONE_EIGHTH_INSTR(value) _NOT_INSTR_(value, _ONE_EIGHTH)

#define COMPARE_INSTR(oper_1, oper_2) BINARY_INTEGRAL_INSTR(oper_1, oper_2, COMPARE)
#define COMPARE_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, COMPARE_FLOAT)

//PUSH_INSTR(float_as_word(oper_1)), PUSH_INSTR(float_as_word(oper_2)), NO_OPERAND_INSTR(instr)
#define BINARY_FLOAT_INSTR(oper_1, oper_2, instr) BINARY_INTEGRAL_INSTR(float_as_word(oper_1), float_as_word(oper_2), instr)
#define ADD_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, ADD_FLOAT)
#define SUBTRACT_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, SUBTRACT_FLOAT)
#define MULTIPLY_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, MULTIPLY_FLOAT)
#define DIVIDE_FLOAT_INSTR(oper_1, oper_2) BINARY_FLOAT_INSTR(oper_1, oper_2, DIVIDE_FLOAT)

#define _CONVERT_TO_FLOAT_(oper_1, from_type, sign) PUSH ## from_type ## _INSTR(oper_1), NO_OPERAND_INSTR(CONVERT_TO_FLOAT_FROM ## sign ## from_type)
#define CONVERT_TO_FLOAT_FROM_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1,,)
#define CONVERT_TO_FLOAT_FROM_HALF_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1, _HALF,)
#define CONVERT_TO_FLOAT_FROM_QUARTER_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1, _QUARTER,)
#define CONVERT_TO_FLOAT_FROM_ONE_EIGHTH_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1, _ONE_EIGHTH,)
#define CONVERT_TO_FLOAT_FROM_SIGNED_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1,,_SIGNED)
#define CONVERT_TO_FLOAT_FROM_SIGNED_HALF_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1, _HALF,_SIGNED)
#define CONVERT_TO_FLOAT_FROM_SIGNED_QUARTER_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1, _QUARTER,_SIGNED)
#define CONVERT_TO_FLOAT_FROM_SIGNED_ONE_EIGHTH_INSTR(oper_1) _CONVERT_TO_FLOAT_(oper_1, _ONE_EIGHTH,_SIGNED)
#define CONVERT_TO_FLOAT_FROM_HALF_FLOAT_INSTR(oper_1) PUSH_HALF_INSTR(half_float_as_half_word_type(oper_1)), NO_OPERAND_INSTR(CONVERT_TO_FLOAT_FROM_HALF_FLOAT)


#define _CONVERT_TO_HALF_FLOAT_(oper_1, from_type, sign) PUSH ## from_type ## _INSTR(oper_1), NO_OPERAND_INSTR(CONVERT_TO_HALF_FLOAT_FROM ## sign ## from_type)
#define CONVERT_TO_HALF_FLOAT_FROM_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1,,)
#define CONVERT_TO_HALF_FLOAT_FROM_HALF_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, _HALF,)
#define CONVERT_TO_HALF_FLOAT_FROM_QUARTER_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, _QUARTER,)
#define CONVERT_TO_HALF_FLOAT_FROM_ONE_EIGHTH_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, _ONE_EIGHTH,)
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, ,_SIGNED)
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_HALF_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, _HALF,_SIGNED)
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_QUARTER_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, _QUARTER,_SIGNED)
#define CONVERT_TO_HALF_FLOAT_FROM_SIGNED_ONE_EIGHTH_INSTR(oper_1) _CONVERT_TO_HALF_FLOAT_(oper_1, _ONE_EIGHTH,_SIGNED)
#define CONVERT_TO_HALF_FLOAT_FROM_FLOAT_INSTR(oper_1) PUSH_INSTR(float_as_word(oper_1)), NO_OPERAND_INSTR(CONVERT_TO_HALF_FLOAT_FROM_FLOAT)


#define CONVERT_TO_INTEGER_INSTR(oper_1) PUSH_INSTR(float_as_word(oper_1)), NO_OPERAND_INSTR(CONVERT_TO_FROM_FLOAT)



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

#define POSTFIX_UPDATE_HALF_INSTR(quantity) SINGLE_OPERAND_INSTR(POSTFIX_UPDATE_HALF, quantity)
#define POSTFIX_UPDATE_QUARTER_INSTR(quantity) SINGLE_OPERAND_INSTR(POSTFIX_UPDATE_QUARTER, quantity)
#define POSTFIX_UPDATE_ONE_EIGHTH_INSTR(quantity) SINGLE_OPERAND_INSTR(POSTFIX_UPDATE_ONE_EIGHTH, quantity)

#define ALLOCATE_INSTR(quantity) SINGLE_OPERAND_INSTR(ALLOCATE, -quantity)

INLINE_FUNC_SIGNATURE(evaluate);

#define re_interpret(value, from_type, to_type)  (((union {to_type to_value; from_type from_value;})(value)).to_value)
#define word_as_float(word) re_interpret(word, word_type, float_type)
#define word_as_float_half(word) re_interpret(word, word_type, half_float_type)
#define half_word_as_float(hw) re_interpret(hw, half_word_type, float_type)
#define half_word_as_float_half(hw) re_interpret((half_word_type)hw, half_word_type, half_float_type)
#define half_float_as_half_word_type(hf) re_interpret((half_float_type)hf, half_float_type, half_word_type)

#define float_as_word(double_value) re_interpret(double_value, float_type, word_type)
#define double_as_signed_word(double_value) re_interpret(double_value, double, signed_word_type)

#define MSB(value) (value >> (word_type)((BYTE_BIT_SIZE * sizeof(word_type)) - 1))

// Macros for updating pointers
#define UPDATE_POINTER(ptr, oper, quantity) (ptr oper##= quantity)

#define _INCREMENT_POINTER_(ptr, mag)       UPDATE_POINTER(ptr, +, mag)
#define INCREMENT_POINTER(ptr)              _INCREMENT_POINTER_(ptr, WORD_SIZE)
#define INCREMENT_POINTER_HALF(ptr)         _INCREMENT_POINTER_(ptr, HALF_WORD_SIZE)
#define INCREMENT_POINTER_QUARTER(ptr)      _INCREMENT_POINTER_(ptr, QUARTER_WORD_SIZE)
#define INCREMENT_POINTER_ONE_EIGHTH(ptr)   _INCREMENT_POINTER_(ptr, ONE_EIGHTH_WORD_SIZE)
#define get_INCREMENT_POINTER(_t_) INCREMENT_POINTER ## _t_

#define _DECREMENT_POINTER_(ptr, mag)       UPDATE_POINTER(ptr, -, mag)
#define DECREMENT_POINTER(ptr)              _DECREMENT_POINTER_(ptr, WORD_SIZE)
#define DECREMENT_POINTER_HALF(ptr)         _DECREMENT_POINTER_(ptr, HALF_WORD_SIZE)
#define DECREMENT_POINTER_QUARTER(ptr)      _DECREMENT_POINTER_(ptr, QUARTER_WORD_SIZE)
#define DECREMENT_POINTER_ONE_EIGHTH(ptr)   _DECREMENT_POINTER_(ptr, ONE_EIGHTH_WORD_SIZE)
#define get_DECREMENT_POINTER(_t_) DECREMENT_POINTER ## _t_

// The stack_pointer is initialized with zero,
// pushing a value decrements the stack_pointer by the size of the value and sets the value in question
// poping returns the current value and increments the stack pointer by the size of the value being popped
// peek simply dereferences the stack pointer by the appropriate pointer type ...
// update simply updates the current value at stack_pointer ...
#define _pop_(sp, _type_, _size_)           (*((_type_ *)(_INCREMENT_POINTER_(sp, _size_)) - 1))
#define pop(sp)                             _pop_(sp, word_type,                        WORD_SIZE)
#define pop_HALF(sp)                        _pop_(sp, half_word_type,                   HALF_WORD_SIZE)
#define pop_QUARTER(sp)                     _pop_(sp, quarter_word_type,                QUARTER_WORD_SIZE)
#define pop_ONE_EIGHTH(sp)                  _pop_(sp, one_eighth_word_type,             ONE_EIGHTH_WORD_SIZE)
#define get_pop(_t_) pop ## _t_

#define _push_(sp, value, _type_, _size_)   ((*(_type_ *)(_DECREMENT_POINTER_(sp, _size_)) = value))
#define push(sp, value)                     _push_(sp, value, word_type,                WORD_SIZE)
#define push_HALF(sp, value)                _push_(sp, value, half_word_type,           HALF_WORD_SIZE)
#define push_QUARTER(sp, value)             _push_(sp, value, quarter_word_type,        QUARTER_WORD_SIZE)
#define push_ONE_EIGHTH(sp, value)          _push_(sp, value, one_eighth_word_type,     ONE_EIGHTH_WORD_SIZE)
#define get_push(_t_) push ## _t_

#define _peek_(sp, _type_, _size_)          (*(_type_ *)(sp))
#define peek(sp)                            _peek_(sp, word_type,                       WORD_SIZE)
#define peek_HALF(sp)                       _peek_(sp, half_word_type,                  HALF_WORD_SIZE)
#define peek_QUARTER(sp)                    _peek_(sp, quarter_word_type,               QUARTER_WORD_SIZE)
#define peek_ONE_EIGHTH(sp)                 _peek_(sp, one_eighth_word_type,            ONE_EIGHTH_WORD_SIZE)
#define get_peek(_t_) peek ## _t_

#define _update_(sp, value, _type_, _size_) (_peek_(sp, _type_, _size_) = value)
#define update(sp, value)                   _update_(sp, value, word_type,              WORD_SIZE)
#define update_HALF(sp, value)              _update_(sp, value, half_word_type,         HALF_WORD_SIZE)
#define update_QUARTER(sp, value)           _update_(sp, value, quarter_word_type,      QUARTER_WORD_SIZE)
#define update_ONE_EIGHTH(sp, value)        _update_(sp, value, one_eighth_word_type,   ONE_EIGHTH_WORD_SIZE)
#define get_update(_t_) update ## _t_

#endif
