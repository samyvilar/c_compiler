#include <stdio.h>
#include <stdlib.h>

#include "cpu.h"
#include "kernel.h"
#include "sys_call_ids.h"

#define NUMBER_OF_FILE_NODES_PER_BLOCK 256

file_node_type
    *file_nodes_block = (file_node_type[]) {[0 ... (NUMBER_OF_FILE_NODES_PER_BLOCK - 1)] = {NULL}},
    *recycle_file_nodes = NULL;

word_type available_file_nodes = NUMBER_OF_FILE_NODES_PER_BLOCK;


#define _new(recycled, _block, _available, _dest_ptr, _next_obj, _quantity) {      \
    if (recycled)                                                   \
        (_dest_ptr = recycled), (recycled = _next_obj(recycled));   \
    else if (_available)                                            \
        _dest_ptr = (_block + --_available);                        \
    else                                                            \
    {                                                               \
        _block = malloc(_quantity * sizeof(*_dest_ptr));            \
        _available = _quantity - 1;                                 \
        _dest_ptr = (_block + _available);                          \
    }                                                               \
}


#define _new_file_node(_dest) _new(recycle_file_nodes, file_nodes_block, available_file_nodes, _dest, next_file_node, NUMBER_OF_FILE_NODES_PER_BLOCK)

#define _file_node_inline(_files, _file_id) {               \
    while (_files && (file_id((file_node_type *)_files) != _file_id))         \
        _files = next_file_node(_files);                    \
}

// de-comment if planning to use ...
//const word_type _instr_sizes_[256] = {INSTRUCTION_SIZES};
//const char *_instr_names_[256] = {INSTRUCTION_NAMES};

INLINE_FUNC_SIGNATURE(evaluate)
{
    register word_type
        _stack_pointer = stack_pointer(cpu),
        _base_pointer = base_pointer(cpu),
        _instr_pointer = instr_pointer(cpu);

    word_type // keep track of initial pointers for exit system call ...
        _initial_stack_pointer = _stack_pointer,
        _initial_base_pointer = _base_pointer;
    
    register word_type _flags = flags(cpu);
    
    /* General purpose registers ... */
    register word_type
        operand_0,
        operand_1,
        operand_2,
        operand_3;

    register void *_temp;
    register float_type float_temp;

    /* OS State ... */
    file_node_type *_opened_files = opened_files(os);
    
    char
        _str_buffer_0[1024],
        _str_buffer_1[1024];

    FILE *file;
    
    #define _BINARY_OPERATION_(_o_, _type_, _size_, peek_func) (                \
        (*((_type_ *)_stack_pointer + 1) _o_##= *((_type_ *)_stack_pointer)),   \
        _INCREMENT_POINTER_(_stack_pointer, _size_)                             \
    )
    #define BINARY_OPERATION(_o_)               _BINARY_OPERATION_(_o_, word_type, WORD_SIZE, peek)
    #define BINARY_OPERATION_HALF(_o_)          _BINARY_OPERATION_(_o_, half_word_type, HALF_WORD_SIZE, peek_HALF)
    #define BINARY_OPERATION_QUARTER(_o_)       _BINARY_OPERATION_(_o_, quarter_word_type, QUARTER_WORD_SIZE, peek_QUARTER)
    #define BINARY_OPERATION_ONE_EIGHTH(_o_)    _BINARY_OPERATION_(_o_, one_eighth_word_type, ONE_EIGHTH_WORD_SIZE, peek_ONE_EIGHTH)
    
    #define FLOATING_BINARY_OPERATION(_o_) (                                            \
        (*((float_type *)_stack_pointer + 1) _o_##= *(float_type *)_stack_pointer),     \
        INCREMENT_POINTER(_stack_pointer)                                               \
    )
    #define FLOATING_BINARY_OPERATION_HALF(_o_) (                                                   \
        (*((half_float_type *)_stack_pointer + 1) _o_##= *(half_float_type *)_stack_pointer),       \
        INCREMENT_POINTER_HALF(_stack_pointer)                                                      \
    )
    
    #define update_cpu(cpu)                                         \
        set_base_pointer(cpu, (word_type)_base_pointer);            \
        set_stack_pointer(cpu, (word_type)_stack_pointer);          \
        set_instr_pointer(cpu, (word_type)_instr_pointer);          \
        set_flags(cpu, _flags)

    #ifdef __clang__
        #pragma clang diagnostic push
        #pragma clang diagnostic ignored "-Winitializer-overrides"
    #endif
        static const void* offsets[] = {INSTR_IMPLEMENTATION_ADDRESS(get_label(INVALID))};
    #ifdef __clang__
        #pragma clang diagnostic pop
    #endif
    
    // all instructions/operands MUST BE word aligned!!!
    #define _instr_operand_(_ip, _type_)    (*(_type_ *)(_ip += WORD_SIZE))
    #define instr_operand(ip)               _instr_operand_(ip, word_type)
    #define instr_operand_HALF(ip)          _instr_operand_(ip, half_word_type)
    #define instr_operand_QUARTER(ip)       _instr_operand_(ip, quarter_word_type)
    #define instr_operand_ONE_EIGHTH(ip)    _instr_operand_(ip, one_eighth_word_type)

    #define start() evaluate_instr(offsets, *(instr_value_type *)_instr_pointer)
    #define done() evaluate_instr(offsets, *(instr_value_type *)INCREMENT_POINTER(_instr_pointer))

    
    start();
    
    
    get_label(PASS):
        done();
    
    #define push_impl(_t_) get_label(PUSH ## _t_): push ## _t_(_stack_pointer, instr_operand ## _t_(_instr_pointer)); done();
    #define pop_impl(_t_) get_label(POP ## _t_): INCREMENT_POINTER ## _t_(_stack_pointer); done();

    #define get_impl_name(name) name ## _impl
    #define get_multi_word_impl(instr) _MAP_(get_impl_name(instr), IMPL_WORD_TYPES);
    MAP(get_multi_word_impl, push, pop);
    
    #define LOAD_REGISTER(value) push(_stack_pointer, (word_type)value)
    #define SET_REGISTER(dest) dest = pop(_stack_pointer)
    
    get_label(LOAD_STACK_POINTER):
        DECREMENT_POINTER(_stack_pointer);
        *(word_type *)_stack_pointer = (word_type)_stack_pointer + WORD_SIZE;
        done();
    
    get_label(SET_STACK_POINTER):
        _stack_pointer = *(word_type *)((word_type)_stack_pointer);
        done();
    
    get_label(ALLOCATE):
        _stack_pointer += instr_operand(_instr_pointer);
        done();

    #define number_of_elements operand_0
    #define source_addr operand_1
    #define dest_addr operand_2
        
    #define dup_single_impl(_type_)                                     \
        get_label(DUP_SINGLE ## _type_):                                \
        operand_0 = peek ## _type_(_stack_pointer);                     \
        push ## _type_(_stack_pointer, operand_0);                      \
        done();
    
    #define swap_single_impl(_type_)                                                    \
        get_label(SWAP_SINGLE ## _type_):                                               \
            (*(get_c_type(_type_) *)_stack_pointer       ^= *((get_c_type(_type_) *)_stack_pointer + 1)),        \
            (*((get_c_type(_type_) *)_stack_pointer + 1) ^= *(get_c_type(_type_) *)_stack_pointer),              \
            (*(get_c_type(_type_) *)_stack_pointer       ^= *((get_c_type(_type_) *)_stack_pointer + 1));        \
            done();

    #define load_single_impl(_type_)                                \
        get_label(LOAD_SINGLE ## _type_):                                  \
            source_addr = pop(_stack_pointer);                      \
            push ## _type_(_stack_pointer, *(get_c_type(_type_) *)source_addr); \
            done();
    
    #define set_single_impl(_type_)                                 \
        get_label(SET_SINGLE ## _type_):                            \
            dest_addr = pop ## _type_(_stack_pointer);              \
            *(get_c_type(_type_) *)dest_addr = peek ## _type_(_stack_pointer);  \
            done();
    
    #define dup_impl(_type_)                                                                                                \
        get_label(DUP ## _type_):                                                                                           \
            number_of_elements = instr_operand(_instr_pointer);                                                             \
                /*increment stack pointer so we can decrement pointer withing expression ...*/                              \
            source_addr = (_stack_pointer + sizeof(get_c_type(_type_))) + ((number_of_elements - 1) * sizeof(get_c_type(_type_)));\
            while (number_of_elements--)                                                                                    \
                push ## _type_(_stack_pointer, *(get_c_type(_type_) *)DECREMENT_POINTER ## _type_(source_addr));              \
            done();

//    get_label(DUP):
//        number_of_elements = instr_operand(_instr_pointer);
//        source_addr = (word_type *)_stack_pointer + number_of_elements; // src
//        while (number_of_elements--) push(_stack_pointer, *source_addr--);
//        done();
    
    #define swap_impl(_type_)                                                                   \
        get_label(SWAP ## _type_):                                                              \
            number_of_elements = instr_operand(_instr_pointer);                                 \
            source_addr = (_stack_pointer + sizeof(get_c_type(_type_)))  + ((number_of_elements - 1) * sizeof(get_c_type(_type_)));\
            dest_addr = source_addr + number_of_elements * sizeof(get_c_type(_type_)); /* other values ...*/                 \
            while (number_of_elements--)                                    \
                (*(get_c_type(_type_) *)(DECREMENT_POINTER ## _type_ (source_addr)) ^= *(get_c_type(_type_) *)(DECREMENT_POINTER ## _type_ (dest_addr))),         \
                (*(get_c_type(_type_) *)dest_addr   ^= *(get_c_type(_type_) *)source_addr),           \
                (*(get_c_type(_type_) *)source_addr ^= *(get_c_type(_type_) *)dest_addr);             \
            done();
    
//    get_label(SWAP):
//        number_of_elements = instr_operand(_instr_pointer);
//        source_addr = (word_type *)_stack_pointer + number_of_elements; // offset
//        dest_addr = source_addr + number_of_elements; // other values ...
//        while (number_of_elements--) (operand_2 = *dest_addr), (*dest_addr-- = *source_addr), (*source_addr-- = operand_2);
//        done();
    
    #define load_impl(_type_)                                                           \
        get_label(LOAD ## _type_):                                                      \
            number_of_elements = instr_operand(_instr_pointer);                         \
            source_addr = pop(_stack_pointer) + number_of_elements * sizeof(get_c_type(_type_));   \
            while (number_of_elements--)                                                \
                push ## _type_(_stack_pointer, *(get_c_type(_type_) *)DECREMENT_POINTER ## _type_(source_addr));\
            done();
    
//    get_label(LOAD):
//        number_of_elements = instr_operand(_instr_pointer);
//        source_addr = (word_type *)pop(_stack_pointer) + number_of_elements;
//        while (number_of_elements--) push(_stack_pointer, *--source_addr);
//        done();
    
    #define set_impl(_type_)                                            \
        get_label(SET ## _type_):                                        \
            number_of_elements = instr_operand(_instr_pointer);         \
            dest_addr = pop(_stack_pointer) - sizeof(get_c_type(_type_));          \
            source_addr = _stack_pointer - sizeof(get_c_type(_type_));                               \
            while (number_of_elements--)                                \
                *(get_c_type(_type_) *)INCREMENT_POINTER ## _type_(dest_addr) = *(get_c_type(_type_) *)INCREMENT_POINTER ## _type_(source_addr);    \
        done();
    
    
//    get_label(SET):
//        number_of_elements = instr_operand(_instr_pointer);
//        dest_addr = (word_type *)pop(_stack_pointer);
//        source_addr = (word_type *)_stack_pointer;
//        while (number_of_elements--) *dest_addr++ = *++source_addr;
//        done();
    
    #define postfix_update_impl(_type_)                                         \
        get_label(POSTFIX_UPDATE ## _type_):                                    \
            source_addr = pop(_stack_pointer);                                  \
            push ## _type_(_stack_pointer, *(get_c_type(_type_) *)source_addr);             \
            *(get_c_type(_type_) *)source_addr += (get_c_type(_type_))instr_operand(_instr_pointer);    \
            done();

//    get_label(POSTFIX_UPDATE):
//        update(
//            _stack_pointer, // replace address with value ...
//            *(word_type *)(source_addr = (word_type *)peek(_stack_pointer))  // copy address for update ...
//        );
//        *source_addr += instr_operand(_instr_pointer); // update value ..
//        done();
    MAP(get_multi_word_impl, dup_single, swap_single, load_single, set_single, dup, swap, load, set, postfix_update);
    #undef number_of_elements
    #undef source_addr
    #undef dest_addr
    
    
    get_label(LOAD_BASE_STACK_POINTER):
        LOAD_REGISTER(_base_pointer);
        done();
    
    get_label(SET_BASE_STACK_POINTER):
        SET_REGISTER(_base_pointer);
        done();
    
    get_label(LOAD_INSTRUCTION_POINTER):
        LOAD_REGISTER(_instr_pointer);
        done();
    
    #define get_load_instr(instr) LOAD_ ## instr
    
    #define prefix_NON(value) NON_ ## value,
    #define prefix_ZERO(value) ZERO_ ## value,
    #define NON_ZERO_FLAGS CARRY_BORROW_FLAG, MOST_SIGNIFICANT_BIT_FLAG
    #define FLAGS                                                                                    \
            MAP(prefix_NON,  MAP(prefix_ZERO, MAP(prefix_NON, NON_ZERO_FLAGS) FLAG) NON_ZERO_FLAGS)  \
            MAP(prefix_ZERO, NON_ZERO_FLAGS) ZERO_FLAG, /* ZERO_* flags */                           \
            NON_ZERO_FLAGS
    
    #define load_flag_impl(instr) get_label(LOAD_ ## instr): LOAD_REGISTER(flag_from_value(_flags, instr ## _INDEX)); done();
    MAP(load_flag_impl, FLAGS);
    
    #define DEFAULT_CARRY_BORROW_FLAGS          (BIT(NON_CARRY_BORROW_FLAG_INDEX) | BIT(NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX))
    #define DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS  (BIT(NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX) | BIT(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
    #define ZERO_RELATED_FLAGS                  (BIT(ZERO_CARRY_BORROW_FLAG_INDEX) | BIT(ZERO_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
    #define NON_ZERO_RELATED_FLAGS              (BIT(NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX) | BIT(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
    
    #define compare_impl(_type_)                                                                                                    \
        get_label(COMPARE ## _type_):                       /* 0xFFFF... if a == b else 0x0000.. */                                 \
            operand_2 = ~(word_type)((operand_1 = *((get_c_type(_type_) *)_stack_pointer + 1) - *(get_c_type(_type_) *)_stack_pointer) == 0) + 1;           \
            _flags = (  BIT(NON_ZERO_FLAG_INDEX)                                                                                    \
                        | (DEFAULT_CARRY_BORROW_FLAGS << (*((get_c_type(_type_) *)_stack_pointer) > *((get_c_type(_type_) *)_stack_pointer + 1)))             \
                        | (DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS << (operand_1 >= MSB_MASK ## _type_()))                               \
                     ) ^ (operand_2 & NON_ZERO_RELATED_FLAGS);                                                                      \
            _flags += (operand_2 & (ZERO_RELATED_FLAGS | BIT(NON_ZERO_FLAG_INDEX)));                                                \
            _stack_pointer += 2 * sizeof(get_c_type(_type_));                                                                       \
            done();
    MAP(compare_impl, IMPL_WORD_TYPES);
    
    #define _HALFword_as_float_HALF half_word_as_float_half
    #define get_float_type(_t_)
    #define compare_float_impl(_type_)                                  \
        get_label(COMPARE_FLOAT ## _type_):                             \
            operand_2 = pop ## _type_(_stack_pointer);                  \
            operand_1 = pop ## _type_(_stack_pointer);                  \
            operand_1 = ~(word_type)(((float_temp = _type_ ## word_as_float ## _type_(operand_1) - _type_ ## word_as_float ## _type_(operand_2))) == 0.0) + 1;  \
            _flags = (BIT(NON_ZERO_FLAG_INDEX) | (DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS << (float_temp < 0.0))) ^ (operand_1 & BIT(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX)); \
            _flags += (operand_1 & (ZERO_RELATED_FLAGS | BIT(NON_CARRY_BORROW_FLAG_INDEX) | BIT(NON_ZERO_FLAG_INDEX)));  \
            done();
    MAP(compare_float_impl, IMPL_FLOAT_TYPES);
    #undef _HALFword_as_float_HALF
    
    
    #define NUMERIC ADD, SUBTRACT, MULTIPLY, DIVIDE
    #define INTEGRAL MOD, SHIFT_LEFT, SHIFT_RIGHT, OR, AND, XOR
    #define BINARY_OPERATORS NUMERIC, INTEGRAL
    #define get_oper(instr) _ ## instr ## _oper
    
    #define _ADD_oper            +
    #define _SUBTRACT_oper       -
    #define _MULTIPLY_oper       *
    #define _DIVIDE_oper         /
    #define _MOD_oper            %
    #define _SHIFT_LEFT_oper     <<
    #define _SHIFT_RIGHT_oper    >>
    #define _OR_oper             |
    #define _AND_oper            &
    #define _XOR_oper            ^
    
    #define BINARY_INTEGRAL(_o_, _t_) BINARY_OPERATION ## _t_(_o_) // not entirely sure why I need to add another layer ... for MAP to work ...
    #define _binary_arithmetic_impl_(instr, _t_) get_label(instr ## _t_): BINARY_INTEGRAL(get_oper(instr), _t_); done();
    #define binary_arithmetic_impl(instr) _binary_arithmetic_impl_(instr,)
    #define binary_arithmetic_HALF_impl(instr) _binary_arithmetic_impl_(instr, _HALF)
    #define binary_arithmetic_QUARTER_impl(instr) _binary_arithmetic_impl_(instr, _QUARTER)
    #define binary_arithmetic_ONE_EIGHTH_impl(instr) _binary_arithmetic_impl_(instr, _ONE_EIGHTH)
    
    #define _binary_arithmetic_impl(_t_) _MAP_(get_impl_name(binary_arithmetic ## _t_), BINARY_OPERATORS)
    MAP(_binary_arithmetic_impl, IMPL_WORD_TYPES);
    
    #define BINARY_NUMERIC(_o_, _t_) FLOATING_BINARY_OPERATION ## _t_(_o_)
    #define binary_numeric_impl(instr) get_label(instr ## _FLOAT): BINARY_NUMERIC(get_oper(instr), ); done();
    #define binary_numeric_HALF_impl(instr) get_label(instr ## _FLOAT_HALF): BINARY_NUMERIC(get_oper(instr), _HALF); done();
    #define _binary_numeric_(_t_) _MAP_(get_impl_name(binary_numeric ## _t_), NUMERIC)
    MAP(_binary_numeric_, IMPL_FLOAT_TYPES);
    
    #define SIGNED_WORD_TYPE signed_word_type
    #define UNSIGNED_WORD_TYPE unsigned_word_type
    #define SIGNED_HALF_WORD_TYPE signed_half_word_type
    #define UNSIGNED_HALF_WORD_TYPE unsigned_half_word_type
    #define SIGNED_QUARTER_WORD_TYPE signed_quarter_word_type
    #define UNSIGNED_QUARTER_WORD_TYPE unsigned_quarter_word_type
    #define SIGNED_ONE_EIGHTH_WORD_TYPE signed_one_eighth_word_type
    #define UNISNGED_ONE_EIGHTH_WORD_TYPE unsigned_one_eighth_word_type
    #define get_signed_type(_t_) SIGNED ## _t_ ## _WORD_TYPE
    #define get_unsigned_type(_t_) UNSIGNED ## _t_ ## _WORD_TYPE
    
    // signed/unsigned Integral types => float type ...
    #define convert_to_float_impl(_t_) get_label(CONVERT_TO_FLOAT ## _FROM ## _t_): update(_stack_pointer, float_as_word((float_type)(signed_word_type)(get_signed_type(_t_))(peek ## _t_(_stack_pointer)))); done();
    #define convert_to_float_from_unsigned_impl(_t_) get_label(CONVERT_TO_FLOAT ## _FROM_UNSIGNED ## _t_): update(_stack_pointer, float_as_word((float_type)(word_type)(peek ## _t_(_stack_pointer)))); done();
    MAP(convert_to_float_impl, IMPL_WORD_TYPES);
    MAP(convert_to_float_from_unsigned_impl, IMPL_WORD_TYPES);

    // float_type(s) => integral types
    #define convert_to_integer_impl(_t_) get_label(CONVERT_TO ## _t_): update ## _t_(_stack_pointer, word_as_float((word_type)peek ## _t_(_stack_pointer))); done();
    #define convert_to_from_half_double_impl(_t_) get_label(CONVERT_TO ## _t_ ## _FROM_HALF_DOUBLE): update ## _t_(_stack_pointer, word_as_float_half((word_type)peek_HALF(_stack_pointer))); done();
    MAP(convert_to_from_half_double_impl, IMPL_WORD_TYPES);
    MAP(convert_to_integer_impl, IMPL_WORD_TYPES);
    
    #define ALL_BUT_NON_WORD_TYPE               _HALF, _QUARTER, _ONE_EIGHTH
    #define ALL_BUT_NON_HALF_WORD_TYPE          _QUARTER, _ONE_EIGHTH,  // the trailing comma is not a bug since WORD is the default type
    #define ALL_BUT_NON_QUARTER_WORD_TYPE       _HALF, _ONE_EIGHTH,
    #define ALL_BUT_NON_ONE_EIGHTH_WORD_TYPE    _HALF, _QUARTER,
    
    #define _convert_integrals_(_from_, _to_) get_label(CONVERT_TO ## _to_ ## _FROM ## _from_): update ## _to_(_stack_pointer, peek ## _to_(_stack_pointer)); done()
    #define convert_to_from_(_t_) _convert_integrals_(_t_,);
    #define convert_to_HALF_from_(_t_) _convert_integrals_(_t_, _HALF);
    #define convert_to_QUARTER_from_(_t_) _convert_integrals_(_t_, _QUARTER);
    #define convert_to_ONE_EIGHTH_from_(_t_) _convert_integrals_(_t_, _ONE_EIGHTH);
    #define convert_integrals_impl(_t_) _MAP_(convert_to ## _t_ ## _from_, ALL_BUT_NON ## _t_ ## _WORD_TYPE);
    MAP(convert_integrals_impl, IMPL_WORD_TYPES);

    #define not_impl(_t_) get_label(NOT ## _t_): update ## _t_(_stack_pointer, ~peek ## _t_(_stack_pointer)); done();
    MAP(not_impl, IMPL_WORD_TYPES);
    
    #define _jump(_ip, value, _o_) evaluate_instr(offsets, *(instr_value_type *)(_ip _o_ (value)))
    #define relative_jump(_ip, magnitude) _jump(_ip, ((magnitude) + WORD_SIZE), +=)
    #define absolute_jump(_ip, addr) _jump(_ip, addr, =)
    
    #ifdef __clang__
        #pragma clang diagnostic push
        #pragma clang diagnostic ignored "-Wunsequenced"
    #endif
    get_label(ABSOLUTE_JUMP):
        absolute_jump(_instr_pointer, pop(_stack_pointer));
    
    get_label(RELATIVE_JUMP): // All jumps assume that the pointers are numeric types ...
        relative_jump(_instr_pointer, instr_operand(_instr_pointer));
    
    #define jump_true_impl(_t_) get_label(JUMP_TRUE ## _t_): relative_jump(_instr_pointer, ((pop ## _t_(_stack_pointer) != 0) * instr_operand(_instr_pointer)));
    MAP(jump_true_impl, IMPL_WORD_TYPES);
    #define jump_false_impl(_t_) get_label(JUMP_FALSE ## _t_): relative_jump(_instr_pointer, ((pop ## _t_(_stack_pointer) == 0) * instr_operand(_instr_pointer)));
    MAP(jump_false_impl, IMPL_WORD_TYPES);
    #ifdef __clang__
        #pragma clang diagnostic pop
    #endif

    // JumpTable implemeneted as binary search ... (it assumes values are sorted ...)
    // With initial operand being the default offset followed by the number of values to comare against
    // followed by the offsets accordingly, both the offsets and values need to be word aligned ...
    #define ptr_to_current_median_value     operand_0
    #define number_of_values_remaining      operand_1
    #define ptr_to_values                   operand_2
    #define default_offset                  operand_3
    #define value(_type_)                   peek ## _type_(_stack_pointer)
    #define number_of_values                (*(word_type *)((word_type)_instr_pointer + WORD_SIZE))
    #define jump_table_impl(_type_)                                         \
        get_label(JUMP_TABLE ## _type_):                                    \
            default_offset = instr_operand(_instr_pointer);                 \
            number_of_values_remaining = number_of_values;                  \
            ptr_to_values = ((word_type)_instr_pointer + 2 * WORD_SIZE); /* skip number of values and default offset */   \
            while (number_of_values_remaining)  \
            {\
                ptr_to_current_median_value = (word_type)((word_type *)ptr_to_values + (number_of_values_remaining >>= 1)); \
                check_median_value ## _type_:\
                    if (value(_type_) == *(get_c_type(_type_) *)ptr_to_current_median_value)   {\
                        INCREMENT_POINTER ## _type_(_stack_pointer); \
                        relative_jump(_instr_pointer, *((word_type *)ptr_to_current_median_value + number_of_values)); } \
                if ((value(_type_) > *(get_c_type(_type_) *)ptr_to_current_median_value) && number_of_values_remaining) \
                {\
                    ptr_to_values = (ptr_to_current_median_value += WORD_SIZE); \
                    if (--number_of_values_remaining)\
                        continue ;\
                    goto check_median_value ## _type_; \
                }\
            }\
            INCREMENT_POINTER ## _type_(_stack_pointer); \
            relative_jump(_instr_pointer, default_offset);
    MAP(jump_table_impl, IMPL_WORD_TYPES);
    #undef ptr_to_values
    #undef ptr_to_current_median_value
    #undef value
    #undef number_of_values
    #undef number_of_values_remaining

    
    get_label(SYSTEM_CALL):
        #define  _return_inline(value, ip, bp)                          \
            **(word_type **)((word_type)bp + WORD_SIZE) = value;        \
            absolute_jump(ip, *(word_type *)((word_type)bp))

        #define SYSTEM_CALL_ID(sys_call) ((unsigned char)sys_call) 
        // assume we don't have have more than 256 system calls, TODO: check on that assumption ...
        switch ((unsigned char)pop(_stack_pointer))
        {
            default:
                printf("Invalid System call " WORD_PRINTF_FORMAT "\n", *(word_type *)_stack_pointer);
                goto end;
                
            case SYSTEM_CALL_ID(SYS_CALL_EXIT):
                // void exit(int return_value);
                operand_1 = *(word_type *)((word_type)_base_pointer + WORD_SIZE);  // get exit status code ...
                // exit has a void return type as such it does not have a pointer for a return value,
                // it just contains the return address ...
                
                _temp = _opened_files;
                while (_temp) // flush all opened files ....
                {
                    file = file_pointer((file_node_type *)_temp);
                    fflush(file); // flush the buffers but let os close the files.
                    _temp = next_file_node(_temp);
                }
                // return from entry point with the exit status code ...
                // reset stack and base_pointer to their initial values ...
                _stack_pointer = _initial_stack_pointer;
                _base_pointer = _initial_base_pointer;
                
                push(_stack_pointer, operand_1); // set return value ...
//                *(word_type *)((word_type)_stack_pointer - sizeof(word_type)) = operand_1;  // set return value ...
                goto end; // stop the machine ...
                
            case SYSTEM_CALL_ID(SYS_CALL_OPEN):
                #define file_path_ptr operand_0
                #define mode_ptr operand_1
                #define _file_id operand_2
                            
                #define file_path _str_buffer_0
                #define file_mode _str_buffer_1
                
                _base_pointer = (word_type)_base_pointer + 2*WORD_SIZE; // temporaly pop return address and pointer for return value ...
                file_path_ptr = pop(_base_pointer);
                mode_ptr = pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 4 * WORD_SIZE; // reset it ...
                _file_id = (word_type)-1;
                
                _temp = (char *)file_path;
                operand_3 = sizeof(file_path);
                while (operand_3-- && (*(char *)_temp++ = *(char *)(file_path_ptr++)));
                if (*(char *)--_temp)
                {
                    printf("File name exceeds %zu characters ... \n", sizeof(file_path));
                    _return_inline((word_type)-1, _instr_pointer, _base_pointer);
                    done();
                }
                
                _temp = file_mode;
                operand_3 = sizeof(file_mode);
                while (operand_3-- && (*(char *)_temp++ = *(char *)(mode_ptr++)));
                if (*(char *)--_temp)
                {
                    printf("File Mode exceeds %zu characters ...\n", sizeof(file_mode));
                    _return_inline((word_type)-1, _instr_pointer, _base_pointer);
                    done();
                }
                
                if ((file = fopen(file_path, file_mode)))
                {
                    _new_file_node(_temp);
                    _file_id = (word_type)fileno(file);
                    set_file_id((file_node_type *)_temp, _file_id);
                    set_file_pointer((file_node_type *)_temp, file);
                    set_next_file_node(_temp, _opened_files);
                    _opened_files = _temp;
                }
                else
                    printf("Failed to opened file %s\n", file_path);
                
                _return_inline(_file_id, _instr_pointer, _base_pointer);
                #undef file_path_ptr
                #undef mode_ptr
                #undef _file_id
                #undef file_path
                #undef file_mode
                done();
                
            case SYSTEM_CALL_ID(SYS_CALL_WRITE):
                #define buffer_ptr operand_0
                #define _file_id operand_1
                #define number_of_bytes operand_2
                
                _base_pointer = (word_type)_base_pointer + 2*WORD_SIZE;
                _file_id = pop(_base_pointer);
                buffer_ptr = pop(_base_pointer);
                number_of_bytes = pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 5 * WORD_SIZE;  // reset it ...
                
                _temp = _opened_files;
                _file_node_inline(_temp, _file_id);
                
                if (_temp)
                {
                    file = file_pointer((file_node_type *)_temp);
                    #define index _file_id
                    index = 0;
                    while (number_of_bytes--)
                    {
                        fputc((int)*(char *)(buffer_ptr + (index++ * WORD_SIZE)), file);
                        if (ferror(file))
                            break ;
                    }
                    #undef index
                    _file_id = (word_type)ferror(file); // ferror should either turn 0 if ok non-zero if failure ...
                    fflush(file);
                }
                else
                {
                    _file_id = (word_type)-1;  // the file has yet to be opened ...
                    printf("Error: file not open!\n");
                }
                _return_inline(_file_id, _instr_pointer, _base_pointer);
                done();
        }
        done();
    
    get_label(HALT):
        goto end;
    
    get_label(INVALID):
        printf("Invalid instruction!\n");
        goto end;
    
end:
    update_cpu(cpu); // update cpu state.
}


