#include <stdio.h>
#include <stdlib.h>

#include "cpu.h"
#include "kernel.h"
#include "sys_call_ids.h"

#define NUMBER_OF_FILE_NODES_PER_BLOCK 256

file_node_type
    *file_nodes_block = (file_node_type[NUMBER_OF_FILE_NODES_PER_BLOCK]){},
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
#ifdef PRINT_INSTRS
    const word_type _instr_sizes_[] = {INSTRUCTION_SIZES};
    const char *_instr_names_[] = {INSTRUCTION_NAMES};
    #define get_instr_name(instr_id) (_instr_names_[instr_id])
#endif

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
    
    #define _BINARY_OPERATION_(_o_, _type_, _size_) (                \
        (*((_type_ *)_stack_pointer + 1) _o_##= *((_type_ *)_stack_pointer)),   \
        _INCREMENT_POINTER_(_stack_pointer, _size_)                             \
    )
    #define BINARY_OPERATION(_o_)               _BINARY_OPERATION_(_o_, word_type,              WORD_SIZE)
    #define BINARY_OPERATION_HALF(_o_)          _BINARY_OPERATION_(_o_, half_word_type,         HALF_WORD_SIZE)
    #define BINARY_OPERATION_QUARTER(_o_)       _BINARY_OPERATION_(_o_, quarter_word_type,      QUARTER_WORD_SIZE)
    #define BINARY_OPERATION_ONE_EIGHTH(_o_)    _BINARY_OPERATION_(_o_, one_eighth_word_type,   ONE_EIGHTH_WORD_SIZE)
    
    #define FLOATING_BINARY_OPERATION(_o_) (                                            \
        (*((float_type *)_stack_pointer + 1) _o_##= *(float_type *)_stack_pointer),     \
        INCREMENT_POINTER(_stack_pointer)                                               \
    )
    #define FLOATING_BINARY_OPERATION_HALF(_o_) (                                                   \
        (*((half_float_type *)_stack_pointer + 1) _o_##= *(half_float_type *)_stack_pointer),       \
        INCREMENT_POINTER_HALF(_stack_pointer)                                                      \
    )
    
    #define update_cpu(cpu)                                             \
        set_base_pointer(cpu,   (word_type)_base_pointer);              \
        set_stack_pointer(cpu,  (word_type)_stack_pointer);             \
        set_instr_pointer(cpu,  (word_type)_instr_pointer);             \
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
    #define get_instr_operand(_t_) instr_operand ## _t_

    #define start() evaluate_instr(offsets, *(instr_value_type *)_instr_pointer)
    #ifdef PRINT_INSTRS
        #define done() printf("%s\n", get_instr_name(*(instr_value_type *)INCREMENT_POINTER(_instr_pointer))); evaluate_instr(offsets, *(instr_value_type *)_instr_pointer)
    #else
        #define done() evaluate_instr(offsets, *(instr_value_type *)INCREMENT_POINTER(_instr_pointer))
    #endif
    #define halt() goto end

    
                    start(); // Start executing instructions ...
    
    
    get_label(PASS):
        done();
    
    #define push_impl(_t_) \
        get_label(PUSH ## _t_): \
            get_push(_t_)(_stack_pointer, get_instr_operand(_t_)(_instr_pointer)); \
            done();

    #define pop_impl(_t_) \
        get_label(POP ## _t_): \
            get_INCREMENT_POINTER(_t_)(_stack_pointer); \
            done();

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

    #define number_of_elements  operand_0
    #define source_addr         operand_1
    #define dest_addr           operand_2
        
    #define dup_single_impl(_t_)                                            \
        get_label(DUP_SINGLE ## _t_):                                       \
            operand_0 = get_peek(_t_)(_stack_pointer);                      \
            get_push(_t_)(_stack_pointer, operand_0);                       \
        done();
    
    #define swap_single_impl(_t_)                                                    \
        get_label(SWAP_SINGLE ## _t_):                                               \
            ( *(get_c_type(_t_) *)_stack_pointer       ^= *((get_c_type(_t_) *)_stack_pointer + 1)),         \
            (*((get_c_type(_t_) *)_stack_pointer + 1)  ^=  *(get_c_type(_t_) *)_stack_pointer),              \
            ( *(get_c_type(_t_) *)_stack_pointer       ^= *((get_c_type(_t_) *)_stack_pointer + 1));         \
            done();

    #define load_single_impl(_t_)                                           \
        get_label(LOAD_SINGLE ## _t_):                                      \
            source_addr = pop(_stack_pointer);                              \
            get_push(_t_)(_stack_pointer, *(get_c_type(_t_) *)source_addr); \
            done();
    
    #define set_single_impl(_t_)                                            \
        get_label(SET_SINGLE ## _t_):                                       \
            dest_addr = pop(_stack_pointer);                                \
            *(get_c_type(_t_) *)dest_addr = get_peek(_t_)(_stack_pointer);  \
            done();
    
    #define _calc_byte_offset(number_of_elements, _t_) ((number_of_elements) * get_c_size(_t_))
    
    #define dup_impl(_t_)                                                                                                   \
        get_label(DUP ## _t_):                                                                                              \
            number_of_elements = instr_operand(_instr_pointer);                                                             \
                /*increment stack pointer so we can decrement pointer withing expression ...*/                              \
            source_addr = (_stack_pointer + get_c_size(_t_)) + _calc_byte_offset(number_of_elements - 1, _t_);            \
            while (number_of_elements--)                                                                                    \
                get_push(_t_)(_stack_pointer, *(get_c_type(_t_) *)get_DECREMENT_POINTER(_t_)(source_addr));                 \
            done();
    
    #define swap_impl(_t_)                                                                   \
        get_label(SWAP ## _t_):                                                              \
            number_of_elements = instr_operand(_instr_pointer);                                 \
            source_addr = ((word_type)_stack_pointer + get_c_size(_t_)) + _calc_byte_offset(number_of_elements - 1, _t_);    \
            dest_addr = source_addr + _calc_byte_offset(number_of_elements, _t_); /* other values ...*/                 \
            while (number_of_elements--)                                    \
                (*(get_c_type(_t_) *)(get_DECREMENT_POINTER(_t_)(source_addr)) ^= *(get_c_type(_t_) *)(get_DECREMENT_POINTER(_t_)(dest_addr))),         \
                (*(get_c_type(_t_) *)dest_addr   ^= *(get_c_type(_t_) *)source_addr),           \
                (*(get_c_type(_t_) *)source_addr ^= *(get_c_type(_t_) *)dest_addr);             \
            done();
    
    #define load_impl(_t_)                                                                                  \
        get_label(LOAD ## _t_):                                                                             \
            number_of_elements = instr_operand(_instr_pointer);                                             \
            source_addr = pop(_stack_pointer) + _calc_byte_offset(number_of_elements, _t_);                 \
            while (number_of_elements--)                                                                    \
                get_push(_t_)(_stack_pointer, *(get_c_type(_t_) *)get_DECREMENT_POINTER(_t_)(source_addr)); \
            done();
    
    #define set_impl(_t_)                                            \
        get_label(SET ## _t_):                                        \
            number_of_elements = instr_operand(_instr_pointer);         \
            dest_addr = pop(_stack_pointer) - get_c_size(_t_);          \
            source_addr = _stack_pointer - get_c_size(_t_);                               \
            while (number_of_elements--)                                \
                *(get_c_type(_t_) *)get_INCREMENT_POINTER(_t_)(dest_addr) = *(get_c_type(_t_) *)get_INCREMENT_POINTER(_t_)(source_addr);    \
        done();
    
    #define postfix_update_impl(_t_)                                         \
        get_label(POSTFIX_UPDATE ## _t_):                                    \
            source_addr = pop(_stack_pointer);                                  \
            get_push(_t_)(_stack_pointer, *(get_c_type(_t_) *)source_addr);             \
            *(get_c_type(_t_) *)source_addr += (get_c_type(_t_))instr_operand(_instr_pointer);    \
            done();

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
    
    #define load_flag_impl(instr) \
        get_label(LOAD_ ## instr): \
            LOAD_REGISTER(flag_from_value(_flags, instr ## _INDEX)); \
            done();
    
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
    #define _binary_arithmetic_impl_(instr, _t_) \
        get_label(instr ## _t_): \
            BINARY_INTEGRAL(get_oper(instr), _t_); \
            done();
    #define binary_arithmetic_impl(instr)               _binary_arithmetic_impl_(instr,)
    #define binary_arithmetic_HALF_impl(instr)          _binary_arithmetic_impl_(instr, _HALF)
    #define binary_arithmetic_QUARTER_impl(instr)       _binary_arithmetic_impl_(instr, _QUARTER)
    #define binary_arithmetic_ONE_EIGHTH_impl(instr)    _binary_arithmetic_impl_(instr, _ONE_EIGHTH)
    
    #define _binary_arithmetic_impl(_t_) _MAP_(get_impl_name(binary_arithmetic ## _t_), BINARY_OPERATORS)
    MAP(_binary_arithmetic_impl, IMPL_WORD_TYPES);
    
    #define BINARY_NUMERIC(_o_, _t_)    FLOATING_BINARY_OPERATION ## _t_(_o_)
    #define binary_numeric_impl(instr) \
        get_label(instr ## _FLOAT): \
            BINARY_NUMERIC(get_oper(instr), ); \
            done();
    #define binary_numeric_HALF_impl(instr) \
        get_label(instr ## _FLOAT_HALF): \
            BINARY_NUMERIC(get_oper(instr), _HALF); \
            done();
    #define _binary_numeric_(_t_) _MAP_(get_impl_name(binary_numeric ## _t_), NUMERIC)
    MAP(_binary_numeric_, IMPL_FLOAT_TYPES);
    
    /** CONVERSIONS ** CONVERSIONS ** CONVERSIONS ** CONVERSIONS ** CONVERSIONS ** CONVERSIONS ** CONVERSIONS ** CONVERSIONS **********/
    
    #define _size_difference_(from_type, to_type) (sizeof(get_c_type(from_type)) - sizeof(get_c_type(to_type)))
    #define _convert_(from_type, to_type, update_value) \
        _stack_pointer = (word_type)_stack_pointer + _size_difference_(from_type, to_type); \
        get_update(to_type)(_stack_pointer, update_value);\
        done();
    
    // unsigned Integral types => float type (c char(1 byte), short(2 bytes), int(4 bytes), long(8 bytes) => (c double))
    #define convert_to_float_impl(_from_type_) \
        get_label(CONVERT_TO_FLOAT_FROM ## _from_type_): \
            _convert_(_from_type_, ,float_as_word(\
                (float_type)(get_unsigned_c_type(_from_type_))(get_peek(_from_type_)(_stack_pointer + _size_difference_(, _from_type_)))))
    MAP(convert_to_float_impl, IMPL_WORD_TYPES);

    // signed Integral types => float type (c char(1 byte), short(2 bytes), int(4 bytes), long(8 bytes) => (c double))
    #define convert_to_float_from_signed_impl(_from_type_) \
        get_label(CONVERT_TO_FLOAT_FROM_SIGNED ## _from_type_): \
            _convert_(_from_type_, ,float_as_word((float_type)(get_signed_c_type(_from_type_))get_peek(_from_type_)(_stack_pointer + _size_difference_(, _from_type_))));
    MAP(convert_to_float_from_signed_impl, IMPL_WORD_TYPES);
    
    
    // unsigned Integral types => half float type (c char, short, int, long => c float)...
    #define convert_to_half_float_impl(_from_type_)\
        get_label(CONVERT_TO_HALF_FLOAT_FROM ## _from_type_):\
            _convert_(\
                _from_type_, \
                _HALF, \
               half_float_as_half_word_type(\
                    (half_float_type)(get_unsigned_c_type(_from_type_))get_peek(_from_type_)(_stack_pointer + _size_difference_(_HALF, _from_type_)))\
            );
    MAP(convert_to_half_float_impl, IMPL_WORD_TYPES);
    
    // signed Integral types => half float type (c char, short, int, long => c float)
    #define convert_to_half_float_from_signed_impl(_from_type_)\
        get_label(CONVERT_TO_HALF_FLOAT_FROM_SIGNED ## _from_type_):\
            _convert_(_from_type_, _HALF, half_float_as_half_word_type((half_float_type)(get_signed_c_type(_from_type_))get_peek(_from_type_)(_stack_pointer + _size_difference_(_HALF, _from_type_))))
    MAP(convert_to_half_float_from_signed_impl, IMPL_WORD_TYPES);
    
    // float => half_float  (c double => c float)
    get_label(CONVERT_TO_HALF_FLOAT_FROM_FLOAT):
        _convert_(, _HALF, half_float_as_half_word_type((half_float_type)word_as_float(peek(_stack_pointer + _size_difference_(_HALF, )))))
    
    // half_float => float (c float => c double)
    get_label(CONVERT_TO_FLOAT_FROM_HALF_FLOAT):
        _convert_(_HALF, ,float_as_word((float_type)(half_word_as_float_half(peek_HALF(_stack_pointer + _size_difference_(, _HALF))))))
    
    // float_type => signed integral types (c double => (char(1 byte), short(2 bytes), int(4 bytes), long(8 bytes))
    #define convert_to_integer_impl(_to_type_) \
        get_label(CONVERT_TO ## _to_type_ ## _FROM_FLOAT): \
            _convert_(, _to_type_, word_as_float(peek(_stack_pointer + _size_difference_(_to_type_, ))))
    MAP(convert_to_integer_impl, IMPL_WORD_TYPES);
    
    // half_float_type => signed integral types (c float => (char(1 byte), short(2 bytes), int(4 bytes), long(8 bytes))
    #define convert_to_from_half_float_impl(_to_type_) \
        get_label(CONVERT_TO ## _to_type_ ## _FROM_HALF_FLOAT): \
            _convert_(_HALF, _to_type_, half_word_as_float_half(peek_HALF(_stack_pointer + _size_difference_(_to_type_, _HALF))))
    MAP(convert_to_from_half_float_impl, IMPL_WORD_TYPES);
    
    
    // integral types <==> integral types (c char, short, int, long <==> c char, short, int, long)
    // (excluding conversion between same types) and (unsigned types) since both of which are redundant,
    // the latter for machines using 2s complement ...
    #define ALL_BUT_NON_WORD_TYPE               _HALF, _QUARTER, _ONE_EIGHTH
    #define ALL_BUT_NON_HALF_WORD_TYPE          _QUARTER, _ONE_EIGHTH,  // the trailing comma is not a bug since WORD is the default type
    #define ALL_BUT_NON_QUARTER_WORD_TYPE       _HALF, _ONE_EIGHTH,
    #define ALL_BUT_NON_ONE_EIGHTH_WORD_TYPE    _HALF, _QUARTER,
    
    // unsigned to unsigned
    #define _convert_integrals_from_unsigned_to_unsigned_(_from_, _to_) \
        get_label(CONVERT_TO ## _to_ ## _FROM ## _from_): \
            _convert_(_from_, _to_, (get_unsigned_c_type(_to_))(get_unsigned_c_type(_from_))get_peek(_from_)(_stack_pointer + _size_difference_(_to_, _from_)))
    
    // signed to signed ...
    #define _convert_integrals_from_signed_to_signed_(_from_, _to_) \
        get_label(CONVERT_TO_SIGNED ## _to_ ## _FROM_SIGNED ## _from_): \
            _convert_(_from_, _to_, (get_signed_c_type(_to_))(get_signed_c_type(_from_))get_peek(_from_)(_stack_pointer + _size_difference_(_to_, _from_)))

    // signed to unsigned
    #define _convert_integrals_from_signed_to_unsigned_(_from_, _to_) \
        get_label(CONVERT_TO ## _to_ ## _FROM_SIGNED ## _from_): \
            _convert_(_from_, _to_, (get_unsigned_c_type(_to_))(get_signed_c_type(_from_))get_peek(_from_)(_stack_pointer + _size_difference_(_to_, _from_)))
    
    // unsigned to signed
    #define _convert_integrals_from_unsigned_to_signed_(_from_, _to_) \
        get_label(CONVERT_TO_SIGNED ## _to_ ## _FROM ## _from_): \
            _convert_(_from_, _to_, (get_signed_c_type(_to_))(get_signed_c_type(_from_))get_peek(_from_)(_stack_pointer + _size_difference_(_to_, _from_)))
    
    #define _convert_integrals_(_from_, _to_) \
        _convert_integrals_from_unsigned_to_unsigned_(_from_, _to_);    \
        _convert_integrals_from_signed_to_signed_(_from_, _to_);        \
        _convert_integrals_from_signed_to_unsigned_(_from_, _to_);      \
        _convert_integrals_from_unsigned_to_signed_(_from_, _to_);
    
    #define convert_to_from_(_from_)               _convert_integrals_(_from_, );
    #define convert_to_HALF_from_(_from_)          _convert_integrals_(_from_, _HALF);
    #define convert_to_QUARTER_from_(_from_)       _convert_integrals_(_from_, _QUARTER);
    #define convert_to_ONE_EIGHTH_from_(_from_)    _convert_integrals_(_from_, _ONE_EIGHTH);
    #define convert_integrals_impl(_to_)           _MAP_(convert_to ## _to_ ## _from_, ALL_BUT_NON ## _to_ ## _WORD_TYPE)
    MAP(convert_integrals_impl, IMPL_WORD_TYPES)
    

    /***************************************************************************************************************************************/
    
    #define not_impl(_t_) get_label(NOT ## _t_): update ## _t_(_stack_pointer, ~peek ## _t_(_stack_pointer)); done();
    MAP(not_impl, IMPL_WORD_TYPES);
    
    #define _jump(_ip, value, _o_) evaluate_instr(offsets, *(instr_value_type *)(_ip _o_ (value)))
    // increase magnitude by one word to account for operand, 0 magnitude simply jumps to the next instruction ...
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
    
    #define jump_true_impl(_t_) \
        get_label(JUMP_TRUE ## _t_): \
            relative_jump(_instr_pointer, ((pop ## _t_(_stack_pointer) != 0) * instr_operand(_instr_pointer)));
    MAP(jump_true_impl, IMPL_WORD_TYPES);
    
    #define jump_false_impl(_t_) \
        get_label(JUMP_FALSE ## _t_): \
            relative_jump(_instr_pointer, ((pop ## _t_(_stack_pointer) == 0) * instr_operand(_instr_pointer)));
    
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
    #define value(_type_)                   get_peek(_type_)(_stack_pointer)
    #define number_of_values                (*(word_type *)((word_type)_instr_pointer + WORD_SIZE)) // _instr_pointer currently is pointing to the first operand (default offset)
    #define initial_ptr_to_values           ((word_type)_instr_pointer + (2 * WORD_SIZE)) // skip default offset and number of values operand ...
    #define jump_table_impl(_type_)                                             \
        get_label(JUMP_TABLE ## _type_):                                        \
            default_offset = instr_operand(_instr_pointer);                     \
            number_of_values_remaining = number_of_values;                      \
            ptr_to_values = initial_ptr_to_values;                              \
            while (number_of_values_remaining)  \
            {\
                ptr_to_current_median_value = (word_type)((word_type *)ptr_to_values + (number_of_values_remaining >>= 1)); \
                check_median_value ## _type_:\
                    if (value(_type_) == *(get_c_type(_type_) *)ptr_to_current_median_value)   \
                    {  \
                        get_INCREMENT_POINTER(_type_)(_stack_pointer); /* pop the value from the stack */\
                        relative_jump(_instr_pointer, *((word_type *)ptr_to_current_median_value + number_of_values)); \
                    } \
                if ((value(_type_) > *(get_c_type(_type_) *)ptr_to_current_median_value) && number_of_values_remaining) \
                {\
                    ptr_to_values = (ptr_to_current_median_value += WORD_SIZE); \
                    if (--number_of_values_remaining) \
                        continue ; \
                    goto check_median_value ## _type_; \
                }\
            }\
            get_INCREMENT_POINTER(_type_)(_stack_pointer); \
            relative_jump(_instr_pointer, default_offset);
    MAP(jump_table_impl, IMPL_WORD_TYPES);
    #undef initial_ptr_to_values
    #undef ptr_to_values
    #undef ptr_to_current_median_value
    #undef value
    #undef number_of_values
    #undef number_of_values_remaining

    
    get_label(SYSTEM_CALL):
        #define  _return_inline(value, ip, bp)                            \
            **(word_type **)((word_type)bp + WORD_SIZE) = value;          \
            absolute_jump(ip, *(word_type *)((word_type)bp))
    
        #define char_c_type                 get_c_type(_ONE_EIGHTH)
    
        #define SYSTEM_CALL_ID(sys_call) ((unsigned char)sys_call)
        // assume we don't have have more than 256 system calls, TODO: check on that assumption ...
        switch ((unsigned char)pop(_stack_pointer))
        {
            default:
                printf("Invalid System call " WORD_PRINTF_FORMAT "\n", *(word_type *)_stack_pointer);
                halt();
                
            case SYSTEM_CALL_ID(SYS_CALL_EXIT):
                // void exit(long long return_value);
                operand_1 = *(word_type *)((word_type)_base_pointer + WORD_SIZE);  // get exit status code ...
                // exit has a void return type as such it does not have a pointer for a return value, it just contains the return address ...
                
                _temp = _opened_files;
                while (_temp) // flush all opened files ....
                {
                    fflush((file = file_pointer((file_node_type *)_temp))); // flush the buffers but let os close the files.
                    _temp = next_file_node(_temp);
                }
                // return from entry point with the exit status code, reset stack and base_pointer to their initial values ...
                _stack_pointer = _initial_stack_pointer;
                _base_pointer = _initial_base_pointer;
                           
                push(_stack_pointer, operand_1); // set return value ...
                halt(); // stop the machine ...
                
            case SYSTEM_CALL_ID(SYS_CALL_OPEN):
                // long long __open__(const char * file_path, const char *mode); // returns file_id on success or -1 of failure.
                #define file_path_ptr operand_0
                #define mode_ptr operand_1
                #define _file_id operand_2
                            
                #define file_path _str_buffer_0
                #define file_mode _str_buffer_1
                
                _base_pointer = (word_type)_base_pointer + 2 * WORD_SIZE; // temporaly pop return address and pointer for return value ...
                file_path_ptr = pop(_base_pointer);
                mode_ptr = pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 4 * WORD_SIZE; // reset it ...
                _file_id = (word_type)-1;
                
                #define _return_negative_one_on_buffer_length(str_array, str_ptr, msg)                                      \
                    _temp = (char *)str_array;                                                                              \
                    operand_3 = sizeof(str_array);                                                                          \
                    while (operand_3-- && (*(char *)_temp++ = *(char *)str_ptr)) str_ptr += sizeof(char_c_type);            \
                    if (*(char *)--_temp)                                                                                   \
                    {                                                                                                       \
                        printf msg;                                                                                         \
                        _return_inline((word_type)-1, _instr_pointer, _base_pointer);                                       \
                        done();                                                                                             \
                    }
    
                _return_negative_one_on_buffer_length(file_path, file_path_ptr, ("File name exceeds %zu characters ... \n", sizeof(file_path)));
                _return_negative_one_on_buffer_length(file_mode, mode_ptr, ("File Mode exceeds %zu characters ...\n", sizeof(file_mode)));
                
                if ((file = fopen(file_path, file_mode)))
                {
                    _file_id = (word_type)fileno(file);
                    _temp = _opened_files;
                    _file_node_inline(_temp, _file_id);
                    if (!_temp)
                    {
                        _new_file_node(_temp);
                        set_file_id((file_node_type *)_temp, _file_id);
                        set_file_pointer((file_node_type *)_temp, file);
                        set_next_file_node(_temp, _opened_files);
                        _opened_files = _temp;
                    }
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
                // long long  __write__(long long file_id, char *buffer, unsigned long long number_of_bytes); returns 0 on success or -1 on failure.
                #define buffer_ptr operand_0
                #define _file_id operand_1
                #define number_of_bytes operand_2
                
                _base_pointer = (word_type)_base_pointer + 2 * WORD_SIZE;
                _file_id = pop(_base_pointer);
                buffer_ptr = pop(_base_pointer);
                number_of_bytes = pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 5 * WORD_SIZE;  // reset it ...
                
                _temp = _opened_files;
                _file_node_inline(_temp, _file_id);
                
                if (_temp)
                {
                    file = file_pointer((file_node_type *)_temp);
                    while (number_of_bytes-- && !ferror(file))
                        fputc((int)*(char_c_type *)buffer_ptr, file), (buffer_ptr += sizeof(char_c_type));
                    _file_id = (word_type)ferror(file); // ferror should either turn 0 if ok non-zero if failure ...
                    fflush(file);
                }
                else
                {
                    _file_id = (word_type)-1;  // the file has yet to be opened ...
                    printf("Error: file not open!\n");
                }
                _return_inline(_file_id, _instr_pointer, _base_pointer);
                done(); // un-reachable code ...

            case SYSTEM_CALL_ID(SYS_CALL_READ):
                // # long long __read__(long long file_id, char *dest, unsigned long long number_of_bytes);
                // returns the number of bytes read or zero if None
                _base_pointer = (word_type)_base_pointer + 2 * WORD_SIZE;
                _file_id = pop(_base_pointer);
                buffer_ptr = pop(_base_pointer);
                number_of_bytes = pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 5 * WORD_SIZE;  // reset it ...
                
                _temp = _opened_files;
                _file_node_inline(_temp, _file_id);
                
                if (_temp)
                {
                    file = file_pointer((file_node_type *)_temp);
                    _file_id = number_of_bytes;
                    while (number_of_bytes-- && ((int)(*(char_c_type *)buffer_ptr = fgetc(file)) != EOF) && !ferror(file))
                        buffer_ptr += sizeof(char_c_type);
                    _file_id -= number_of_bytes;
                }
                else
                {
                    _file_id = 0;  // the file has yet to be opened ...
                    printf("Error: file not open!\n");
                }
                _return_inline(_file_id, _instr_pointer, _base_pointer);
                done();
        }
        done();
    
    get_label(HALT):
        halt();
    
    get_label(INVALID):
        printf("Invalid instruction!\n");
        halt();
    
end:
    update_cpu(cpu); // update cpu state.
}


