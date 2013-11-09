/*
 DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED
 DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED
 DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED
 DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED
 */

#include <stdio.h>

#include "vm_1.h"
#include "cpu_0.h"
#include "kernel.h"
#include "bit_hash.h"

#define SYSTEM_CALL_ID
#define NUMBER_OF_FRAMES_PER_BLOCK 256

frame_type
    // use initial block to avoid expensive malloc for small applications.
    *frame_blocks = (frame_type []){[0 ... (NUMBER_OF_FRAMES_PER_BLOCK - 1)] = {NULL}},
    *recycle_frames = NULL;
word_type available_frames = NUMBER_OF_FRAMES_PER_BLOCK;

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

#define _new_frame(_dest) _new(recycle_frames, frame_blocks, available_frames, _dest, next_frame, NUMBER_OF_FRAMES_PER_BLOCK)
#define _new_file_node(_dest) _new(recycle_file_nodes, file_nodes_block, available_file_nodes, _dest, next_file_node, NUMBER_OF_FILE_NODES_PER_BLOCK)

#define _file_node_inline(_files, _file_id) {               \
    while (_files && (file_id((file_node_type *)_files) != _file_id))         \
        _files = next_file_node(_files);                    \
}

const word_type _instr_sizes_[256] = {INSTRUCTION_SIZES};
const char *_instr_names_[256] = {INSTRUCTION_NAMES};



INLINE_FUNC_SIGNATURE(evaluate) {
    register word_type
        _stack_pointer = stack_pointer(cpu),
        _instr_pointer = instr_pointer(cpu),
        _base_pointer = base_pointer(cpu);
    
    register word_type _flags = flags(cpu);
    
    /* Frames ... */
    frame_type
        *_frames = frames(cpu),
        *_temp_frame;
    
    /* General purpose registers ... */
    register word_type
        temp,
        operand_0,
        operand_1,
        operand_2,
        operand_3;
    
    register double float_temp;
    /* OS State ... */
    file_node_type
        *_opened_files = opened_files(os),
        *_files;
    
    char
        *_str_buffer_temp,
        _str_buffer_0[1024],
        _str_buffer_1[1024];
    
    FILE *file;
    
    /* Virtual Memory address translation variables ... */
    register word_type __addr, __hash;
    register void *__temp;

    #define _translate_address_unsafe(mem, addr, dest)  \
        TRANSLATE_ADDRESS_INLINE(mem, addr, dest, __hash, __temp)
    
    #define _translate_instr_address_unsafe _translate_address_unsafe
    
    #define _get_word_inline_unsafe(mem, addr, dest) _translate_address_unsafe(mem, addr, dest); dest = *(word_type *)dest
    #define _set_word_inline_unsafe(mem, addr, value, dest) _translate_address_unsafe(mem, addr, dest); *(word_type *)dest = value
    
    #define _get_instr_word_inline_unsafe _get_word_inline_unsafe
    
    #define _pop_word_inline_unsafe(mem, sp, dest) ++sp; _get_word_inline_unsafe(mem, sp, dest)
    #define _push_word_inline_unsafe(mem, sp, value, dest) _set_word_inline_unsafe(mem, sp, value, dest); sp--
        
    #define _move_word_inline_unsafe(mem, src, dest)            \
        _translate_address_unsafe(mem, src, temp);              \
        _translate_address_unsafe(mem, dest, operand_3);        \
        *(word_type *)operand_3 = *(word_type *)temp
    
    #define _move_word_from_instr_to_stack_inline_unsafe _move_word_inline_unsafe
    
    #define _swap_word_inline_unsafe(mem, src_0, src_1)     \
        _translate_address_unsafe(mem, src_0, temp);        \
        _translate_address_unsafe(mem, src_1, operand_3);   \
        __addr = *(word_type *)temp;                        \
        *(word_type *)temp = *(word_type *)operand_3;       \
        *(word_type *)operand_3 = __addr
        
    #define INCREMENT_POINTER(value) (++value)
    #define DECREMENT_POINTER(value) (--value)
    #define INCREMENT_POINTER_TWICE(value) (value += 2 * WORD_SIZE)
        
    #define UPDATE_INSTR_POINTER INCREMENT_POINTER
    #define UPDATE_INSTR_POINTER_WIDE INCREMENT_POINTER_TWICE
    
    #define _BINARY_OPERATION(_o_, oper_0, oper_1, result, msb_func)    \
        result = INCREMENT_POINTER(_stack_pointer) + 1;                 \
        _translate_address_unsafe(mem, result, oper_0);                 \
        _translate_address_unsafe(mem, _stack_pointer, oper_1);         \
        *(word_type *)oper_0 _o_##= *(word_type *)oper_1;
    
    #define BINARY_OPERATION(_o_)  _BINARY_OPERATION(_o_, operand_0, operand_1, temp, MSB)
    
    #define FLOATING_BINARY_OPERATION(_o_)                          \
        temp = INCREMENT_POINTER(_stack_pointer) + 1;               \
        _translate_address_unsafe(mem, temp, operand_0);            \
        _translate_address_unsafe(mem, _stack_pointer, operand_1);  \
        *(float_type *)operand_0 _o_##= *(float_type *)operand_1;
    
    #define UPDATE_CURRENT_STACK_ELEMENT(_stack_pointer, temp_var, address_var, _new_value) \
        temp_var = _stack_pointer + 1;                                                      \
        _translate_address_unsafe(mem, temp_var, address_var);                              \
        *(word_type *)address_var = _new_value;
    
    #define update_cpu(cpu)                             \
        set_base_pointer(cpu, _base_pointer);           \
        set_stack_pointer(cpu, _stack_pointer);         \
        set_instr_pointer(cpu, _instr_pointer);         \
        set_flags(cpu, _flags);                         \
        set_frames(cpu, _frames)
    
    #define _consume_instruction_operand_inline(mem, ip, destination)   \
        _get_word_inline_unsafe(mem, ip, destination);                  \
        UPDATE_INSTR_POINTER(ip);
    
    const void* offsets[] = {INSTR_IMPLEMENTATION_ADDRESS(get_label(INVALID))};
    
    #define done() goto execute_instruction
    execute_instruction:
        _get_instr_word_inline_unsafe(mem, _instr_pointer, temp);
        UPDATE_INSTR_POINTER(_instr_pointer);
        evaluate_instr(offsets, temp);

        get_label(PASS):
            done();
        
        get_label(PUSH):
            _move_word_from_instr_to_stack_inline_unsafe(mem, _instr_pointer, _stack_pointer);
            DECREMENT_POINTER(_stack_pointer);
            UPDATE_INSTR_POINTER(_instr_pointer);
            done();
            
        get_label(POP):
            INCREMENT_POINTER(_stack_pointer);
            done();
            
        #define number_of_elements operand_0
        #define src_address operand_1
        #define dest_address operand_2
        get_label(LOAD):
            _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
            _pop_word_inline_unsafe(mem, _stack_pointer, src_address);
            src_address += number_of_elements;
            
            while (number_of_elements--)
            {
                DECREMENT_POINTER(src_address);
                _move_word_inline_unsafe(mem, src_address, _stack_pointer);
                DECREMENT_POINTER(_stack_pointer);
            }
            done();
            
        get_label(SET):
            _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
            _pop_word_inline_unsafe(mem, _stack_pointer, dest_address);
            src_address = _stack_pointer;

            while (number_of_elements--)
            {
                INCREMENT_POINTER(src_address);
                _move_word_inline_unsafe(mem, src_address, dest_address);
                INCREMENT_POINTER(dest_address);
            }
            done();

        get_label(POSTFIX_UPDATE):
            _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
            temp = _stack_pointer + 1;
            _translate_address_unsafe(mem, temp, dest_address); // translate dest_address ...
            _translate_address_unsafe(mem, *(word_type *)dest_address, src_address); // translate source address ...
            *(word_type *)dest_address = (*(word_type *)src_address); // push value (replace address by value)...
            *(word_type *)src_address += number_of_elements; // postfix, update and set value ...
            done();


        get_label(DUP):
            _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
            src_address = _stack_pointer + operand_0; // src
            
            while (number_of_elements--)
            {
                _move_word_inline_unsafe(mem, src_address, _stack_pointer);
                DECREMENT_POINTER(src_address);
                DECREMENT_POINTER(_stack_pointer);
            }
            done();
            
        get_label(SWAP):
            _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
            src_address = _stack_pointer + number_of_elements; // offset
            dest_address = src_address + number_of_elements; // other values ...
            
            while (number_of_elements--)
            {
                _swap_word_inline_unsafe(mem, src_address, dest_address); // method_3
                DECREMENT_POINTER(src_address);
                DECREMENT_POINTER(dest_address);
            }
            done();
        #undef number_of_elements
        #undef src_address
        #undef dest_address
                    
        #define LOAD_REGISTER(reg) _push_word_inline_unsafe(mem, _stack_pointer, reg, temp)
        #define SET_REGISTER(reg) _pop_word_inline_unsafe(mem, _stack_pointer, reg)
        get_label(LOAD_BASE_STACK_POINTER):
            LOAD_REGISTER(_base_pointer);
            done();
            
        get_label(SET_BASE_STACK_POINTER):
            SET_REGISTER(_base_pointer);
            done();
            
        get_label(LOAD_STACK_POINTER):
            _set_word_inline_unsafe(mem, _stack_pointer, _stack_pointer, temp);
            DECREMENT_POINTER(_stack_pointer);
            done();
            
        get_label(SET_STACK_POINTER):
            INCREMENT_POINTER(_stack_pointer);
            _get_word_inline_unsafe(mem, _stack_pointer, _stack_pointer);
            done();
            
        get_label(ALLOCATE):
            _consume_instruction_operand_inline(mem, _instr_pointer, temp);
            _stack_pointer += temp;
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
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_1);
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);

            #define DEFAULT_CARRY_BORROW_FLAGS (bit(NON_CARRY_BORROW_FLAG_INDEX) | bit(NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX))
            #define DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS (bit(NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX) | bit(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
            #define ZERO_RELATED_FLAGS (bit(ZERO_CARRY_BORROW_FLAG_INDEX) | bit(ZERO_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
            #define NON_ZERO_RELATED_FLAGS (bit(NON_ZERO_NON_CARRY_BORROW_FLAG_INDEX) | bit(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX))
            #if defined __x86_64__ && 0 // it seemst to be slower probably since its only using 3 registers ...
                #define X86_CARRY_BORROW_FLAG_INDEX 0
                #define X86_ZERO_FLAG_INDEX 6
                #define X86_MOST_SIGNIFICANT_BIT_INDEX 7
                #define X86_FLAGS_MASK (bit(X86_ZERO_FLAG_INDEX) | bit(X86_CARRY_BORROW_FLAG_INDEX) | bit(X86_MOST_SIGNIFICANT_BIT_INDEX))
                #define FLAGS_MASK (bit(ZERO_FLAG_INDEX) | bit(CARRY_BORROW_FLAG_INDEX) | bit(MOST_SIGNIFICANT_BIT_FLAG_INDEX))
                
                asm(
                    "cmpq %2, %1\n\t"   // compare the two values ...
                    "pushfq\n\t"        // push x86 eflags register
                    "popq %1\n\t"       // (pop it) saving it ...
                    
                    // calculate/set carry borrow related flag(s) ...
                    "movq %1, %%rcx\n\t"  // move x86_flags into cl register (shl reg, reg => can only be done with the CL reg holding the magniture)
                    "andb $1, %%cl\n\t"   // clear all other flags from cl register, cl will either be 1 (CARRY_BORROW flag was set) or 0 (CARRY_BORROW wasn't set)
                    "movq %4, %2\n\t"     // set default mask msb...010100 into operand_1 (this assumes CARRY_BORROW wasn't set)
                    "shlq %%cl, %2\n\t"   // shifts the default mask inverting NON_CARRY_BORROW_FLAG if cl is 1 which implies CARRY_BORROW was set
                                          // otherwise masks remains which implies the carry borrow flag was indeed not set...
                    "movq %2, %0\n\t"     // copy/save carry_borrow flags into _flags ...

                    // calculate/set zero flags
                    "movq %1, %2\n\t"   // move x86 flags into operand_1
                    "shrq $6, %2\n\t"   // move zero into lsb position
                    "andq $1, %2\n\t"   // clear all other flags ... operand_1 will either be 1 (ZeroFlag was set) or 0 (ZeroFlag wasn't set)
                    "addq $1, %2\n\t"   // adding one will set the Non-Zero Flag leaving Zero flag with 0, or invert the Non-ZeroFlag with value 0 and setting the Zero Flag with 1
                    "orq %2, %0\n\t"    // save the zero/non-zero flag with carry borrow flag calculations so we can use operand_1 for msb calculations

                    // calculate/set most significant bit related flags
                    "shrq $7, %1\n\t"    // move msb flag into zeroth position, either 0 (sign bit was set) or 1 (sign bit wasn't set) ...
                    "andq $1, %1\n\t" // clear any other remaining flags
                    "movq %1, %%rcx\n\t" // move operand_0 into cl register
                    "movq %5, %2\n\t"    // set default mask for msb....0101.0000.00 (indicating most significant bit wasn't set)
                    "shlq %%cl, %2\n\t"  // shifts the default mask to the left either by 1 indicating that the sign bit was set or 0 which means that indeed the sign bit wasn't set
                    "orq %2, %0\n\t"     // save the msb related flags with the zero and carry borrow related flags ...

                    // at this point _flags contains all 3 groups of flags set, operand_0 and operand_1 are free for use ....
                    // calculate the Non-Zero-Or-* | Non-Zero-And-* related flags...
                    "movq %0, %1\n\t"
                    "rorq $2, %1\n\t"   // shift the second bit (zeroth-bit) into the msb location
                    "sarq $63, %1\n\t"  // will produce either -1 if the zeroth flag was set or 0 if it wasn't
                    "andq %6, %1\n\t" // clear all other flags,
                    "orq %1, %0\n\t" // update those flags we are interested in (Zero-Or-*) flags ...
                    
                    // calculate Non-Zero-And-* flags ...
                    "notq %1\n\t"     // either -1 if the the non-zero flag was set or ~(272) if the zero flag was set ...
                    "sarq $1, %1\n\t"  // shift to the right to align for adjacing Non-Zero related flags
                    "andq %1, %0\n\t"  // clear or leave unchange Non-Zero-And-* related flags ...
                    
                    :   "=&r"(_flags) // '=' write only (output), '&' it will be clobbered early on result may be in a diff register, 'r' means operand in register ...
                    :   "r"(operand_0),
                        "r"(operand_1),
                        "i"(X86_FLAGS_MASK),
                        "i"(DEFAULT_CARRY_BORROW_FLAGS),
                        "i"(DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS),
                        "i"(ZERO_RELATED_FLAGS)
                    : "rcx"
                );
        #else
            // convert zero flag to => 0xFFFFFFF..., non-zero flag => 0
            operand_2 = ~(word_type)((temp = operand_0 - operand_1) == 0) + 1;
            _flags = (
                bit(NON_ZERO_FLAG_INDEX) // assume non-zero
                      |
                // calculate carry borrow flags, (set non_carry or shift setting carry borrow inverting non-carry-*) ...
                (DEFAULT_CARRY_BORROW_FLAGS << (operand_1 > operand_0))
                      |
                // calculate most significant bit flag, (set non_msb or shift setting msb inverting non-msb-*) ...
                (DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS << (word_type)(temp >= MSB_MASK(word_type)))
            )
                ^ // calculate Non-Zero-And-* flags ...
           (operand_2 & NON_ZERO_RELATED_FLAGS);
            // calculate ZERO_FALG, ZERO_OR_CARRY_BORROW_FLAG, ZERO_OR_MOST_SIGNIFICANT_BIT_FLAG
            // in this case we are checking our previous NonZero assumption,
            // if it was wrong adding will invert it, setting the adjacing ZeroFlag
            // or leaves it be if indeed the solution is non-zero ....
            _flags += (operand_2 & (ZERO_RELATED_FLAGS | bit(NON_ZERO_FLAG_INDEX)));
        #endif
        done();

        get_label(COMPARE_FLOAT):
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_1);
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
            // SEE: COMPARE!
            // 0 => 0, 1 => 0xFFFFFFFFF
            operand_0 = ~(word_type)(((float_temp = word_as_float(operand_0) - word_as_float(operand_1))) == 0.0) + 1;
            _flags = (
                bit(NON_ZERO_FLAG_INDEX)
                |
                (DEFAULT_MOST_SIGNIFICANT_BIT_FLAGS << (float_temp < 0.0))  // set msb related flags ...
            ) ^ (operand_0 & bit(NON_ZERO_NON_MOST_SIGNIFICANT_BIT_FLAG_INDEX));
            // NON_CARRY_BORROW_FLAG_INDEX is used to check for >= (it needs to be set if the ZeroFlag is set)
            _flags += (operand_0 & (ZERO_RELATED_FLAGS | bit(NON_CARRY_BORROW_FLAG_INDEX) | bit(NON_ZERO_FLAG_INDEX)));
            done();

        get_label(ADD):
            BINARY_OPERATION(+)
            done();
            
        get_label(SUBTRACT):
            BINARY_OPERATION(-)
            done();
            
        get_label(MULTIPLY):
            BINARY_OPERATION(*)
            done();
            
        get_label(DIVIDE):
            BINARY_OPERATION(/)
            done();
            
        get_label(MOD):
            BINARY_OPERATION(%)
            done();
            
        get_label(SHIFT_LEFT):
            BINARY_OPERATION(<<)
            done();
            
        get_label(SHIFT_RIGHT):
            BINARY_OPERATION(>>)
            done();
            
        get_label(OR):
            BINARY_OPERATION(|)
            done();
            
        get_label(AND):
            BINARY_OPERATION(&)
            done();
            
        get_label(XOR):
            BINARY_OPERATION(^)
            done();
            
        get_label(ADD_FLOAT):
            FLOATING_BINARY_OPERATION(+)
            done();
            
        get_label(SUBTRACT_FLOAT):
            FLOATING_BINARY_OPERATION(-)
            done();
            
        get_label(MULTIPLY_FLOAT):
            FLOATING_BINARY_OPERATION(*)
            done();
            
        get_label(DIVIDE_FLOAT):
            FLOATING_BINARY_OPERATION(/)
            done();
            
        get_label(CONVERT_TO_FLOAT):
            UPDATE_CURRENT_STACK_ELEMENT(
                _stack_pointer,
                operand_2,
                operand_1,
                float_as_word((float_type)(signed_word_type)*(word_type *)operand_1)
            );
            done();
            
        get_label(CONVERT_TO_FLOAT_FROM_UNSIGNED):
            UPDATE_CURRENT_STACK_ELEMENT(
                _stack_pointer,
                operand_2,
                operand_1,
                float_as_word((float_type)*(word_type *)operand_1)
            );
            done();
            
        get_label(CONVERT_TO_INTEGER):
            UPDATE_CURRENT_STACK_ELEMENT(
                _stack_pointer,
                operand_2,
                operand_1,
                word_as_float(*(word_type *)operand_1)
            );
            done();
            
        get_label(NOT):
            UPDATE_CURRENT_STACK_ELEMENT(
                _stack_pointer,
                operand_2,
                operand_1,
                ~*(word_type *)operand_1
            );
            done();
            
        get_label(ABSOLUTE_JUMP):
            _pop_word_inline_unsafe(mem, _stack_pointer, _instr_pointer);
            done();
            
        get_label(RELATIVE_JUMP):
            _consume_instruction_operand_inline(mem, _instr_pointer, operand_0);
            _instr_pointer += operand_0;
            done();
            
        get_label(JUMP_TRUE):
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
            _consume_instruction_operand_inline(mem, _instr_pointer, operand_1);
            _instr_pointer += (operand_0 != 0) * operand_1;
            done();
            
        get_label(JUMP_FALSE):
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
            _consume_instruction_operand_inline(mem, _instr_pointer, operand_1);
            _instr_pointer += (operand_0 == 0) * operand_1;
            done();

        get_label(JUMP_TABLE):  // JumpTable implemeneted as binary search ... (it assumes values are sorted ...)
            #define number_of_values operand_0
            #define value operand_1
            #define median_value operand_2
    
            temp = ++_instr_pointer;
            _consume_instruction_operand_inline(mem, _instr_pointer, number_of_values);  // number of values ...
            operand_3 = number_of_values;  // save a copy to calculate offset ...
            _pop_word_inline_unsafe(mem, _stack_pointer, value);  // get value

            while (number_of_values)
            {
                __addr = _instr_pointer + (number_of_values >>= 1);  // number_of_values /= 2; cut the search space in half.
                check_median_value:
                    _get_word_inline_unsafe(mem, __addr,  median_value);
                    if (value == median_value)
                    {
                        __addr += operand_3;
                        _get_instr_word_inline_unsafe(mem, __addr, _instr_pointer);
                        _instr_pointer += temp;
                        done();
                    }
                
                if ((value > median_value) && number_of_values)  // the value we are seeking is greater than the median and we still have values to work with ...
                {
                    _instr_pointer = ++__addr;  // _instr_pointer += number_of_values-- + 1; value must be in greater half, remove the lower half ...
                    if (--number_of_values) // if we haven't removed all the values continue ...
                        continue ;
                    goto check_median_value; // all values have being removed, check that the current value is the one we are seeking...
                }
            }
            _get_instr_word_inline_unsafe(mem, (temp - 1), _instr_pointer); // value wasn't found so read default offset.
            _instr_pointer += temp;
            done();
            #undef number_of_values
            #undef value
            #undef median_value

        get_label(PUSH_FRAME):
            _new_frame(_temp_frame);
            set_frames_base_pointer(_temp_frame, _base_pointer);
            set_frames_stack_pointer(_temp_frame, _stack_pointer);
            set_next_frame(_temp_frame, _frames); // save the rest of the frames.
            _frames = _temp_frame; // add the frame
            done();
            
        get_label(POP_FRAME):
            _base_pointer = frames_base_pointer(_frames);  // update base and stack pointer.
            _stack_pointer = frames_stack_pointer(_frames);
            
            _temp_frame = _frames; // save the frame for recycling.
            _frames = next_frame(_frames); // remove the frame
            
            set_next_frame(_temp_frame, recycle_frames);  // save the rest of the recycled fames.
            recycle_frames = _temp_frame;  // recycle frame.
            done();
            
        get_label(SYSTEM_CALL):
            _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
            _base_pointer += 3 * WORD_SIZE; // assuming that all system calls return a value
            // those that don't (exit ...) must update the _base_pointer to account for the omitted return value ...
            #define _consume_parameter_inline(bs, mem, dest) _get_word_inline_unsafe(mem, bs, dest); INCREMENT_POINTER(bs)

            #define _set_str_inline(addr, dest, mem, char_buffer, max_length) {     \
                _get_word_inline_unsafe(mem, addr, dest);                           \
                while (max_length-- && (*char_buffer++ = dest))                     \
                    ++addr;                                                         \
                --char_buffer;                                                      \
            }
            
            #define  _return_inline(value, mem, ip, bp, dest) { \
                INCREMENT_POINTER(bp); /* assume that on return the frame will be popped updating _base_pointer */\
                _get_word_inline_unsafe(mem, bp, ip); /* returning to caller  */\
                INCREMENT_POINTER(bp);    \
                _get_word_inline_unsafe(mem, bp, dest); /* get location of return values storage */\
                _set_word_inline_unsafe(mem, dest, value, bp); /* actually returning the value */\
            }
            
            
            switch ((unsigned char)operand_0)
            {
                default:
                    printf("Invalid System call " WORD_PRINTF_FORMAT "\n", operand_0);
                    goto end;
                    
                case SYSTEM_CALL_ID(SYS_CALL_EXIT):
                    // void exit(int return_value);
                    --_base_pointer; // account for omitted pointer for return value, being a void system call
                    _get_word_inline_unsafe(mem, _base_pointer, operand_0);  // get exit status ...
                    // since this is a function call there must be at least 2 frames, exits and mains ...
                    // pop all frames ... (look for return address of main ...)

                    // get entry point, base and stack pointers ...
                    while (next_frame( (_temp_frame = next_frame(_frames)) ))
                        _frames = _temp_frame;
                    _base_pointer = frames_base_pointer(_frames);
                    _frames = next_frame(_frames); // remove frame leaving only entry points ...
                    
                    _files = _opened_files;
                    while (_files) // flush all opened files ....
                    {
                        file = file_pointer(_files);
                        fflush(file); // flush the buffers but let os close the files.
                        _files = next_file_node(_files);
                    }

                    _return_inline(operand_0, mem, _instr_pointer, _base_pointer, operand_1);
                    break ;
                
                case SYSTEM_CALL_ID(SYS_CALL_OPEN):
                    #define file_path_ptr operand_0
                    #define mode_ptr operand_1
                    #define _file_id operand_2
                    #define file_path _str_buffer_0
                    #define file_mode _str_buffer_1
                    _consume_parameter_inline(_base_pointer, mem, file_path_ptr);
                    _consume_parameter_inline(_base_pointer, mem, mode_ptr);
                    _base_pointer -= (2 + 3) * WORD_SIZE; // reset base_pointer 2 operands and 3 poitners.
                    _file_id = (word_type)-1;
                    
                    _str_buffer_temp = file_path;
                    operand_3 = sizeof(file_path);
                    _set_str_inline(file_path_ptr, temp, mem, _str_buffer_temp, operand_3);
                    if (*_str_buffer_temp)
                    {
                        printf("File name exceeds %zu characters ... \n", sizeof(file_path));
                        _return_inline((word_type)-1, mem, _instr_pointer, _base_pointer, operand_0);
                        break ;
                    }
                    
                    _str_buffer_temp = file_mode;
                    operand_3 = sizeof(file_mode);
                    _set_str_inline(mode_ptr, temp, mem, _str_buffer_temp, operand_3);
                    if (*_str_buffer_temp)
                    {
                        printf("File Mode exceeds %zu characters ...\n", sizeof(file_mode));
                        _return_inline((word_type)-1, mem, _instr_pointer, _base_pointer, operand_0);
                        break ;
                    }
                    
                    if ((file = fopen(file_path, file_mode)))
                    {
                        _new_file_node(_files);
                        _file_id = (word_type)fileno(file);
                        set_file_id(_files, _file_id);
                        set_file_pointer(_files, file);
                        set_next_file_node(_files, _opened_files);
                        _opened_files = _files;
                    }
                    else
                        printf("Failed to opened file %s\n", file_path);
                    
                    _return_inline(_file_id, mem, _instr_pointer, _base_pointer, operand_0);
                    #undef file_path_ptr
                    #undef mode_ptr
                    #undef _file_id
                    #undef file_path
                    #undef file_mode
                    break ;
                
                case SYSTEM_CALL_ID(SYS_CALL_WRITE):
                    #define _file_id operand_0
                    #define buffer_ptr operand_1
                    #define number_of_bytes operand_2
                    _consume_parameter_inline(_base_pointer, mem, _file_id);
                    _consume_parameter_inline(_base_pointer, mem, buffer_ptr);
                    _consume_parameter_inline(_base_pointer, mem, number_of_bytes);
                    _base_pointer -= (3 + 3) * WORD_SIZE; // reset base pointer for return call.
                    _files = _opened_files;
                    _file_node_inline(_files, _file_id);
                
                    if (_files)
                    {
                        file = file_pointer(_files);
                        while (number_of_bytes--)
                        {
                            _get_word_inline_unsafe(mem, buffer_ptr, temp);
                            ++buffer_ptr;
                            fputc((int)temp, file);
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
                    _return_inline(_file_id, mem, _instr_pointer, _base_pointer, temp);
                    break ;
            }
            done();
            #undef _file_id
            #undef buffer_ptr
            #undef number_of_bytes


        get_label(HALT):
            goto end;

        get_label(INVALID):
            printf("Invalid instruction!\n");
            goto end;
        
    goto execute_instruction;
    
    end:
        update_cpu(cpu); // update cpu state.
}