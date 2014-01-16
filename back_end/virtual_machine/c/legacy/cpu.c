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

    word_type
        _initial_stack_pointer = _stack_pointer,
        _initial_base_pointer = _base_pointer;
    
    register word_type _flags = flags(cpu);
    
    /* General purpose registers ... */
    register word_type
        *temp,
        *operand_0,
        operand_1,
        operand_2,
        operand_3;

    register void *_temp;
    register double float_temp;

    /* OS State ... */
    file_node_type *_opened_files = opened_files(os);
    
    char
        _str_buffer_0[1024],
        _str_buffer_1[1024];

    FILE *file;
    
    #define PTR_UPDATE_MAGNITUDE WORD_SIZE
    #define INCREMENT_POINTER(ptr) (ptr += PTR_UPDATE_MAGNITUDE)
    #define DECREMENT_POINTER(ptr) (ptr -= PTR_UPDATE_MAGNITUDE)
    
    #define pop(sp) (*(word_type *)INCREMENT_POINTER(sp))
    #define push(sp, value) ((*(word_type *)sp = value), DECREMENT_POINTER(sp))
        
    #define peek(sp) (*(word_type *)((word_type)sp + WORD_SIZE))
    #define update(sp, value) peek(sp) = value
    
    #define BINARY_OPERATION(_o_) ((INCREMENT_POINTER(_stack_pointer)), (peek(_stack_pointer) _o_##= *(word_type *)_stack_pointer))
    #define FLOATING_BINARY_OPERATION(_o_) (INCREMENT_POINTER(_stack_pointer), (*(float_type *)(_stack_pointer + WORD_SIZE) _o_##= *(float_type *)_stack_pointer))
    
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
    
    #define done() evaluate_instr(offsets, pop(_instr_pointer))
    #define instr_operand pop

    evaluate_instr(offsets, *(word_type *)_instr_pointer); // start execution ...
    
    get_label(PASS):
        done();
    
    get_label(PUSH):
        push(_stack_pointer, instr_operand(_instr_pointer));
        done();
    
    get_label(POP):
        INCREMENT_POINTER(_stack_pointer);
        done();

    #define LOAD_REGISTER(reg) push(_stack_pointer, (word_type)reg)
    #define SET_REGISTER(reg) reg = pop(_stack_pointer)
    
    get_label(LOAD_STACK_POINTER):
        // The standard does not dictate which operand (during a binary expression) is first evaluated only the end result is guaranteed
        // as such gcc (as of 4.8.1) during assignment actually evaluates the left operand first then the right
        // while clang and icc evaluate the right operand first then the left ...
        // @@due note that clang during ++/-- (unlike gcc < 4.8.1 / icc) actually use the updated value if referenced again
        // in the expression (the original value remains in the register and reused again ...)
        // ex: a[index] = index++ assuming index = 0, is actually a[1] = 0 in clang and gcc 4.8.1
        // while in icc/gcc 4.7.2 its a[0] = 0
        // both icc and clang define __GNUC__ but clang defines __clang__ and icc defines __INTEL_COMPILER
        // not entirely sure if this is worth it ... specially when clang will emit a warning ... (hence we need to temporaryly silenece it)
    
        #ifdef __clang__
            #pragma clang diagnostic push
            #pragma clang diagnostic ignored "-Wunsequenced"
        #endif
    
        #if defined(__GNUC__) && !defined(__clang__) && !defined(__INTEL_COMPILER)
            *(word_type *)_stack_pointer = (word_type)_stack_pointer;
            DECREMENT_POINTER(_stack_pointer);
        #else
            push(_stack_pointer, (word_type)_stack_pointer);
        #endif
    
        #ifdef __clang__
            #pragma clang diagnostic pop
        #endif
    
        done();
    
    get_label(SET_STACK_POINTER):
        _stack_pointer = *(word_type *)((word_type)_stack_pointer + WORD_SIZE);
        done();
    
    get_label(ALLOCATE):
        _stack_pointer += instr_operand(_instr_pointer);
        done();

    #define number_of_elements operand_1
    #define source_addr temp
    #define dest_addr operand_0
    get_label(DUP):
        number_of_elements = instr_operand(_instr_pointer);
        source_addr = (word_type *)_stack_pointer + number_of_elements; // src
        while (number_of_elements--) push(_stack_pointer, *source_addr--);
        done();
    
    get_label(SWAP):
        number_of_elements = instr_operand(_instr_pointer);
        source_addr = (word_type *)_stack_pointer + number_of_elements; // offset
        dest_addr = source_addr + number_of_elements; // other values ...
        while (number_of_elements--) (operand_2 = *dest_addr), (*dest_addr-- = *source_addr), (*source_addr-- = operand_2);
        done();
    
    get_label(LOAD):
        number_of_elements = instr_operand(_instr_pointer);
        source_addr = (word_type *)pop(_stack_pointer) + number_of_elements;
        while (number_of_elements--) push(_stack_pointer, *--source_addr);
        done();
    
    get_label(SET):
        number_of_elements = instr_operand(_instr_pointer);
        dest_addr = (word_type *)pop(_stack_pointer);
        source_addr = (word_type *)_stack_pointer;
        while (number_of_elements--) *dest_addr++ = *++source_addr;
        done();
    
    get_label(POSTFIX_UPDATE):
        update(
            _stack_pointer, // replace address with value ...
            *(word_type *)(source_addr = (word_type *)peek(_stack_pointer))  // copy address for update ...
        );
        *source_addr += instr_operand(_instr_pointer); // update value ..
        done();
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
    
    get_label(LOAD_ZERO_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, ZERO_FLAG_INDEX));
        done();
    
    get_label(LOAD_NON_ZERO_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, NON_ZERO_FLAG_INDEX));
        done();
    
    get_label(LOAD_CARRY_BORROW_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, CARRY_BORROW_FLAG_INDEX));
        done();
    
    get_label(LOAD_NON_CARRY_BORROW_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, NON_CARRY_BORROW_FLAG_INDEX));
        done();
    
    get_label(LOAD_MOST_SIGNIFICANT_BIT_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, MOST_SIGNIFICANT_BIT_FLAG_INDEX));
        done();
    
    get_label(LOAD_NON_MOST_SIGNIFICANT_BIT_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX));
        done();
    
    get_label(LOAD_ZERO_CARRY_BORROW_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, ZERO_CARRY_BORROW_FLAG_INDEX));
        done();
    
    get_label(LOAD_NON_ZERO_NON_CARRY_BORROW_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX));
        done();

    get_label(LOAD_ZERO_MOST_SIGNIFICANT_BIT_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, ZERO_MOST_SIGNIFICANT_BIT_FLAG_INDEX));
        done();
    
    get_label(LOAD_NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG):
        LOAD_REGISTER(flag_from_value(_flags, NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX));
        done();
    
    get_label(COMPARE):
        #define DEFAULT_CARRY_BORROW_FLAGS MASK(NON_CARRY_BORROW_FLAG_INDEX, NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX)
        #define DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS MASK(NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX, NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX)
        #define ZERO_RELATED_FLAGS MASK(ZERO_CARRY_BORROW_FLAG_INDEX, ZERO_MOST_SIGNIFICANT_BIT_FLAG_INDEX)
        #define NON_ZERO_RELATED_FLAGS MASK(NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX, NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX)
    
        INCREMENT_POINTER(_stack_pointer);
        operand_2 = ~(word_type)((operand_1 = peek(_stack_pointer) - *(word_type *)_stack_pointer) == 0) + 1; // 0 ==> 0, 1 ==> 0xFFFF...
        _flags = (
            MASK(NON_ZERO_FLAG_INDEX) // assume non-zero
            |
            // calculate carry borrow flags, (set non_carry or shift setting carry borrow inverting non-carry-*) ...
            (DEFAULT_CARRY_BORROW_FLAGS << (*(word_type *)_stack_pointer > peek(_stack_pointer)))
            |
            // calculate most significant bit flag, (set non_msb or shift setting msb inverting non-msb-*) ...
            (DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS << (word_type)(operand_1 >= MSB_MASK(word_type)))
        ) ^ (operand_2 & NON_ZERO_RELATED_FLAGS) // calculate Non-Zero-And-* flags ...
        ;
        // calculate ZERO_FALG, ZERO_OR_CARRY_BORROW_FLAG, ZERO_OR_MOST_SIGNIFICANT_BIT_FLAG
        // in this case we are checking our previous NonZero assumption,
        // if it was wrong adding will invert it, setting the adjacing ZeroFlag
        // or leaves it be if indeed the solution is non-zero ....
        _flags += (operand_2 & (ZERO_RELATED_FLAGS | MASK(NON_ZERO_FLAG_INDEX)));
        INCREMENT_POINTER(_stack_pointer);
        done();
    
    get_label(COMPARE_FLOAT):
        operand_2 = pop(_stack_pointer);
        operand_1 = pop(_stack_pointer);
        // SEE: COMPARE!
        // 0 => 0, 1 => 0xFFFFFFFFF
        operand_1 = ~(word_type)(((float_temp = word_as_float(operand_1) - word_as_float(operand_2))) == 0.0) + 1;
        _flags = (
              MASK(NON_ZERO_FLAG_INDEX)
              |
              (DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS << (float_temp < 0.0))  // set msb related flags ...
              ) ^ (operand_1 & MASK(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
        ;
        // NON_CARRY_BORROW_FLAG_INDEX is used to check for >= (it needs to be set if the ZeroFlag is set)
        _flags += (operand_1 & (ZERO_RELATED_FLAGS | MASK(NON_CARRY_BORROW_FLAG_INDEX, NON_ZERO_FLAG_INDEX)));
        done();
    
    get_label(ADD):
        BINARY_OPERATION(+);
        done();
    
    get_label(SUBTRACT):
        BINARY_OPERATION(-);
        done();
    
    get_label(MULTIPLY):
        BINARY_OPERATION(*);
        done();
    
    get_label(DIVIDE):
        BINARY_OPERATION(/);
        done();
    
    get_label(MOD):
        BINARY_OPERATION(%);
        done();
    
    get_label(SHIFT_LEFT):
        BINARY_OPERATION(<<);
        done();
    
    get_label(SHIFT_RIGHT):
        BINARY_OPERATION(>>);
        done();
    
    get_label(OR):
        BINARY_OPERATION(|);
        done();
    
    get_label(AND):
        BINARY_OPERATION(&);
        done();
    
    get_label(XOR):
        BINARY_OPERATION(^);
        done();
    
    get_label(ADD_FLOAT):
        FLOATING_BINARY_OPERATION(+);
        done();
    
    get_label(SUBTRACT_FLOAT):
        FLOATING_BINARY_OPERATION(-);
        done();
    
    get_label(MULTIPLY_FLOAT):
        FLOATING_BINARY_OPERATION(*);
        done();
    
    get_label(DIVIDE_FLOAT):
        FLOATING_BINARY_OPERATION(/);
        done();
    
    get_label(CONVERT_TO_FLOAT):
        update(
            _stack_pointer,
            float_as_word((float_type)(signed_word_type)peek(_stack_pointer))
        );
        done();

    get_label(CONVERT_TO_FLOAT_FROM_UNSIGNED):
        update(
            _stack_pointer,
           float_as_word((float_type)peek(_stack_pointer))
        );
        done();
    
    get_label(CONVERT_TO_INTEGER):
        update(_stack_pointer, word_as_float(peek(_stack_pointer)));
        done();
    
    get_label(NOT):
        update(_stack_pointer, ~peek(_stack_pointer));
        done();
    
    #define _jump(_ip, value, _o_) evaluate_instr(offsets, *(word_type *)(_ip _o_ (value)))
    #define relative_jump(_ip, magnitude) _jump(_ip, ((magnitude) + WORD_SIZE), +=) // evaluate_instr(offsets, *(word_type *)(_ip += (magnitude) + WORD_SIZE))
    #define absolute_jump(_ip, addr) _jump(_ip, addr, =)
    get_label(ABSOLUTE_JUMP):
        absolute_jump(_instr_pointer, pop(_stack_pointer));
    
    get_label(RELATIVE_JUMP): // All jumps now assume that the pointers are numeric types ...
        relative_jump(_instr_pointer, instr_operand(_instr_pointer));
    
    get_label(JUMP_TRUE):
        relative_jump(_instr_pointer, ((pop(_stack_pointer) != 0) * instr_operand(_instr_pointer)));

    get_label(JUMP_FALSE):
        relative_jump(_instr_pointer, ((pop(_stack_pointer) == 0) * instr_operand(_instr_pointer)));
    
    get_label(JUMP_TABLE):  // JumpTable implemeneted as binary search ... (it assumes values are sorted ...)
        // With initial operand being the default offset followed by the number of values to comare against ...
        #define ptr_to_values                   temp
        #define ptr_to_current_median_value     operand_0
        #define number_of_values_remaining      operand_1
        #define value                           operand_2
        #define default_offset                  operand_3
        #define number_of_values                (*(word_type *)((word_type)_instr_pointer + WORD_SIZE))
    
        value = pop(_stack_pointer);
        default_offset = instr_operand(_instr_pointer);
        number_of_values_remaining = number_of_values;
        ptr_to_values = (word_type *)((word_type)_instr_pointer + 2*WORD_SIZE); //  acount for default_offset, number_of_values operand
    
        while (number_of_values_remaining)
        {
            ptr_to_current_median_value = ptr_to_values + (number_of_values_remaining >>= 1); // cut the search space in half.
            check_median_value:
                if (value == *ptr_to_current_median_value)
                    relative_jump(_instr_pointer, *(ptr_to_current_median_value + number_of_values));
            
            if ((value > *ptr_to_current_median_value) && number_of_values_remaining)  // the value we are seeking is greater than the median and we still have values to work with ...
            {
                ptr_to_values = ++ptr_to_current_median_value;  // value must be in greater half, remove lower half ...
                if (--number_of_values_remaining) // if we haven't removed all the values continue ...
                    continue ;
                goto check_median_value; // all values have being removed, check that the current value is the one we are seeking...
            }
        }
        relative_jump(_instr_pointer, default_offset); // could not locate value use default offset ...
        #undef ptr_to_values
        #undef ptr_to_current_median_value
        #undef value
        #undef number_of_values
        #undef number_of_values_remaining
    
    get_label(SYSTEM_CALL):
        #define  _return_inline(value, ip, bp)                          \
            **(word_type **)((word_type)bp + 2*WORD_SIZE) = value;    \
            absolute_jump(ip, *(word_type *)((word_type)bp + WORD_SIZE))

        #define SYSTEM_CALL_ID(sys_call) ((unsigned char)sys_call) // assume we don't have have more than 256 system calls, TODO: check on that assumption ...
        switch ((unsigned char)pop(_stack_pointer))
        {
            default:
                printf("Invalid System call " WORD_PRINTF_FORMAT "\n", *(word_type *)_stack_pointer);
                goto end;
                
            case SYSTEM_CALL_ID(SYS_CALL_EXIT):
                // void exit(int return_value);
                operand_1 = *(word_type *)((word_type)_base_pointer + 2 * WORD_SIZE);  // get exit status code ...
                // exit has void return type as such it does not have a pointer for a return value,
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
                *(word_type *)_stack_pointer = operand_1;  // set return value ...
                goto end; // stop the machine ...
                
            case SYSTEM_CALL_ID(SYS_CALL_OPEN):
                #define file_path_ptr operand_0
                #define mode_ptr temp
                #define _file_id operand_2
                            
                #define file_path _str_buffer_0
                #define file_mode _str_buffer_1
                
                _base_pointer = (word_type)_base_pointer + 2*WORD_SIZE; // temporaly pop return address and pointer for return value ...
                file_path_ptr = (word_type *)pop(_base_pointer);
                mode_ptr = (word_type *)pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 4*WORD_SIZE; // reset it ...
                
                _file_id = (word_type)-1;
                
                _temp = file_path;
                operand_3 = sizeof(file_path);
                while (operand_3-- && (*(char *)_temp++ = *file_path_ptr++));
                if (*(char *)--_temp)
                {
                    printf("File name exceeds %zu characters ... \n", sizeof(file_path));
                    _return_inline((word_type)-1, _instr_pointer, _base_pointer);
                    break ;
                }
                
                _temp = file_mode;
                operand_3 = sizeof(file_mode);
                while (operand_3-- && (*(char *)_temp++ = *mode_ptr++));
                if (*(char *)--_temp)
                {
                    printf("File Mode exceeds %zu characters ...\n", sizeof(file_mode));
                    _return_inline((word_type)-1, _instr_pointer, _base_pointer);
                    break ;
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
                #define _file_id operand_1
                #define buffer_ptr temp
                #define number_of_bytes operand_2
                
                _base_pointer = (word_type)_base_pointer + 2*WORD_SIZE;
                _file_id = pop(_base_pointer);
                buffer_ptr = (word_type *)pop(_base_pointer);
                number_of_bytes = pop(_base_pointer);
                _base_pointer = (word_type)_base_pointer - 5*WORD_SIZE;  // reset it ...
                
                _temp = _opened_files;
                _file_node_inline(_temp, _file_id);
                
                if (_temp)
                {
                    file = file_pointer((file_node_type *)_temp);
                    while (number_of_bytes--)
                    {
                        fputc((int)*buffer_ptr++, file);
                        if (ferror(file))
                            break ;
                    }
                    _file_id = (word_type)ferror(file); // ferrror should either turn 0 if ok non-zero if failure ...
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


