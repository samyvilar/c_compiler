/**/
#include <stdio.h>
#include <xmmintrin.h>

#include "fast_vm.h"
#include "cpu.h"
#include "kernel.h"

#define INSTR_ID(instr_id) ((unsigned char)instr_id)
#define SYSTEM_CALL_ID INSTR_ID
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
    while (_files && (file_id(_files) != _file_id))         \
        _files = next_file_node(_files);                    \
}

const word_type _instr_sizes_[256] = {INSTRUCTION_SIZES};

INLINE_FUNC_SIGNATURE(evaluate) {
    /* x86 has 8 (so call) general purpose registers, x86_64 doubles that to 16 ...*/
    /* x86 (RAX, RBX, RCX, RDX) index (RSI (source), RDI (destination), RBP (base pointer), RSP (stack pointer)) */
    /* x86_64 (R8-R15) and SSE (XMM0 - XMM15) 128 bit registers (should be quite common today) */
    /* CPU State ... */
    
    register word_type
        _stack_pointer asm("r14") = stack_pointer(cpu),
        _instr_pointer asm("r15") = instr_pointer(cpu),
        _base_pointer = base_pointer(cpu),
        _zero_flag = zero_flag(cpu),
        _msb_flag = most_significant_bit_flag(cpu),
        _carry_borrow_flag = carry_borrow_flag(cpu);
    
    /* Frames ... */
    register frame_type
        *_frames = frames(cpu),
        *_temp_frame;
    
    /* General purpose registers ... */
    register word_type
        temp,
        operand_0,
        operand_1,
        operand_2,
        operand_3;
    
    // registers xmm0, xmm1, xmm2
    register float_type
        float_temp,
        float_operand_0,
        float_operand_1;
    
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

    #define _translate_address_unsafe(mem, addr, dest) \
        TRANSLATE_ADDRESS_INLINE(mem, addr, dest, __hash, __temp)
    
    #define _get_word_inline_unsafe(mem, addr, dest) _translate_address_unsafe(mem, addr, dest); dest = *(word_type *)dest
    #define _set_word_inline_unsafe(mem, addr, value, dest) _translate_address_unsafe(mem, addr, dest); *(word_type *)dest = value
    
    #define _pop_word_inline_unsafe(mem, sp, dest) ++sp; _get_word_inline_unsafe(mem, sp, dest)
    #define _push_word_inline_unsafe(mem, sp, value, dest) _set_word_inline_unsafe(mem, sp, value, dest); sp--
        
    #define _move_word_inline_unsafe(mem, src, dest)        \
        _translate_address_unsafe(mem, src, temp);           \
        _translate_address_unsafe(mem, dest, operand_3);     \
        *(word_type *)operand_3 = *(word_type *)temp
        
    #define _swap_word_inline_unsafe(mem, src_0, src_1)     \
        _translate_address_unsafe(mem, src_0, temp);        \
        _translate_address_unsafe(mem, src_1, operand_3);   \
        __addr = *(word_type *)temp;                         \
        *(word_type *)temp = *(word_type *)operand_3;       \
        *(word_type *)operand_3 = __addr
        
        
    #define INCREMENT_POINTER(value) (++value)
    #define DECREMENT_POINTER(value) (--value)
    #define INCREMENT_POINTER_TWICE(value) (value += 2 * WORD_SIZE)
        
    #define UPDATE_INSTR_POINTER(_ip) ++_ip
    #define UPDATE_INSTR_POINTER_WIDE(_ip) _ip += 2
        
        
    #define _BINARY_OPERATION(_o_, oper_0, oper_1, result, msb_func)    \
        _pop_word_inline_unsafe(mem, _stack_pointer, oper_1);           \
            result = _stack_pointer + 1;                                \
          _translate_address_unsafe(mem, result, operand_2);            \
        oper_0 = *(word_type *)operand_2;                               \
        result = oper_0 _o_ oper_1;                                     \
        *(word_type *)operand_2 = result;                               \
        _zero_flag = !result;                                           \
        _msb_flag = msb_func(result);
        
    #define BINARY_OPERATION(_o_)  _BINARY_OPERATION(_o_, operand_0, operand_1, temp, MSB)
        
    #define LESS_THAN_ZERO(value) ((value) < 0.0)
    #define FLOATING_BINARY_OPERATION(_o_)                          \
        _pop_word_inline_unsafe(mem, _stack_pointer, operand_1);    \
        float_operand_1 = word_as_float(operand_1);                 \
            temp = _stack_pointer + 1;                            \
            _translate_address_unsafe(mem, temp, operand_2);      \
        float_operand_0 = word_as_float(*(word_type *)operand_2);   \
        float_temp = float_operand_0 _o_ float_operand_1;           \
        *(word_type *)operand_2 = float_as_word(float_temp);        \
        _zero_flag = !float_temp;                                   \
        _msb_flag = float_temp < 0.0;

    #define update_cpu(cpu)                             \
        set_base_pointer(cpu, _base_pointer);           \
        set_stack_pointer(cpu, _stack_pointer);         \
        set_instr_pointer(cpu, _instr_pointer);         \
        set_zero_flag(cpu, _zero_flag);                 \
        set_carry_borrow_flag(cpu, _carry_borrow_flag); \
        set_most_significant_bit_flag(cpu, _msb_flag);  \
        set_frames(cpu, _frames);
        
    #define cache_cpu(cpu)                              \
        _base_pointer = base_pointer(cpu);              \
        _stack_pointer = stack_pointer(cpu);            \
        _instr_pointer = instr_pointer(cpu);            \
        _zero_flag = zero_flag(cpu);                    \
        _carry_borrow_flag = carry_borrow_flag(cpu);    \
        _msb_flag = most_significant_bit_flag(cpu);     \
        _frames = frames(cpu);
        
    #define _consume_instruction_operand_inline(mem, ip, destination)   \
        UPDATE_INSTR_POINTER(ip);                                       \
        _get_word_inline_unsafe(mem, ip, destination);                  \
        UPDATE_INSTR_POINTER(ip);

        
    #define calculate_offset_address(initial_label, label) (&&label - &&initial_label)
    #define get_label(instr) _ ## instr ## _ ## IMPLEMENTATION
    const word_type offsets[] = {
        [0 ... 255] = calculate_offset_address(_evaluate_instr, get_label(INVALID)),
        
        [PASS] = calculate_offset_address(_evaluate_instr, get_label(PASS)),
        [PUSH] = calculate_offset_address(_evaluate_instr, get_label(PUSH)),
        [POP] = calculate_offset_address(_evaluate_instr, get_label(POP)),
        [LOAD] = calculate_offset_address(_evaluate_instr, get_label(LOAD)),
        [SET] = calculate_offset_address(_evaluate_instr, get_label(SET)),
        [DUP] = calculate_offset_address(_evaluate_instr, get_label(DUP)),
        [SWAP] = calculate_offset_address(_evaluate_instr, get_label(SWAP)),
        
        [LOAD_BASE_STACK_POINTER] = calculate_offset_address(_evaluate_instr, get_label(LOAD_BASE_STACK_POINTER)),
        [SET_BASE_STACK_POINTER] = calculate_offset_address(_evaluate_instr, get_label(SET_BASE_STACK_POINTER)),
        [LOAD_STACK_POINTER] = calculate_offset_address(_evaluate_instr, get_label(LOAD_STACK_POINTER)),
        [SET_STACK_POINTER] = calculate_offset_address(_evaluate_instr, get_label(SET_STACK_POINTER)),
        [ALLOCATE] = calculate_offset_address(_evaluate_instr, get_label(ALLOCATE)),

        [ADD] = calculate_offset_address(_evaluate_instr, get_label(ADD)),
        [SUBTRACT] = calculate_offset_address(_evaluate_instr, get_label(SUBTRACT)),
        [MULTIPLY] = calculate_offset_address(_evaluate_instr, get_label(MULTIPLY)),
        [DIVIDE] = calculate_offset_address(_evaluate_instr, get_label(DIVIDE)),
        [MOD] = calculate_offset_address(_evaluate_instr, get_label(MOD)),
        [SHIFT_LEFT] = calculate_offset_address(_evaluate_instr, get_label(SHIFT_LEFT)),
        [SHIFT_RIGHT] = calculate_offset_address(_evaluate_instr, get_label(SHIFT_RIGHT)),
        [OR] = calculate_offset_address(_evaluate_instr, get_label(OR)),
        [AND] = calculate_offset_address(_evaluate_instr, get_label(AND)),
        [XOR] = calculate_offset_address(_evaluate_instr, get_label(XOR)),
        
        [ADD_FLOAT] = calculate_offset_address(_evaluate_instr, get_label(ADD_FLOAT)),
        [SUBTRACT_FLOAT] = calculate_offset_address(_evaluate_instr, get_label(SUBTRACT_FLOAT)),
        [MULTIPLY_FLOAT] = calculate_offset_address(_evaluate_instr, get_label(MULTIPLY_FLOAT)),
        [DIVIDE_FLOAT] = calculate_offset_address(_evaluate_instr, get_label(DIVIDE_FLOAT)),
        
        [CONVERT_TO_FLOAT] = calculate_offset_address(_evaluate_instr, get_label(CONVERT_TO_FLOAT)),
        [CONVERT_TO_FLOAT_FROM_UNSIGNED] = calculate_offset_address(_evaluate_instr, get_label(CONVERT_TO_FLOAT_FROM_UNSIGNED)),
        [CONVERT_TO_INTEGER] = calculate_offset_address(_evaluate_instr, get_label(CONVERT_TO_INTEGER)),
        
        [NOT] = calculate_offset_address(_evaluate_instr, get_label(NOT)),
        
        [ABSOLUTE_JUMP] = calculate_offset_address(_evaluate_instr, get_label(ABSOLUTE_JUMP)),
        [RELATIVE_JUMP] = calculate_offset_address(_evaluate_instr, get_label(RELATIVE_JUMP)),
        [JUMP_TRUE] = calculate_offset_address(_evaluate_instr, get_label(JUMP_TRUE)),
        [JUMP_FALSE] = calculate_offset_address(_evaluate_instr, get_label(JUMP_FALSE)),
        [JUMP_TABLE] = calculate_offset_address(_evaluate_instr, get_label(JUMP_TABLE)),
        
        [LOAD_ZERO_FLAG] = calculate_offset_address(_evaluate_instr, get_label(LOAD_ZERO_FLAG)),
        [LOAD_CARRY_BORROW_FLAG] = calculate_offset_address(_evaluate_instr, get_label(LOAD_CARRY_BORROW_FLAG)),
        [LOAD_MOST_SIGNIFICANT_BIT_FLAG] = calculate_offset_address(_evaluate_instr, get_label(LOAD_MOST_SIGNIFICANT_BIT_FLAG)),
        
        [PUSH_FRAME] = calculate_offset_address(_evaluate_instr, get_label(PUSH_FRAME)),
        [POP_FRAME] = calculate_offset_address(_evaluate_instr, get_label(POP_FRAME)),
        
        [SYSTEM_CALL] = calculate_offset_address(_evaluate_instr, get_label(SYSTEM_CALL)),
        
        [HALT] = calculate_offset_address(_evaluate_instr, get_label(HALT))
    };
    
    #define done() goto execute_instruction
    #define evaluate_instr(instr_id) goto *(&&_evaluate_instr + offsets[instr_id])
    
    execute_instruction:
        _get_word_inline_unsafe(mem, _instr_pointer, temp);
        evaluate_instr(temp);
    
        _evaluate_instr:
            get_label(PASS):
                INCREMENT_POINTER(_instr_pointer);
                done();
            
            get_label(PUSH):
                UPDATE_INSTR_POINTER(_instr_pointer);
                _move_word_inline_unsafe(mem, _instr_pointer, _stack_pointer);
                DECREMENT_POINTER(_stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(POP):
                INCREMENT_POINTER(_stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
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
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SET_BASE_STACK_POINTER):
                SET_REGISTER(_base_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(LOAD_STACK_POINTER):
                _set_word_inline_unsafe(mem, _stack_pointer, _stack_pointer, temp);
                DECREMENT_POINTER(_stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SET_STACK_POINTER):
                INCREMENT_POINTER(_stack_pointer);
                _get_word_inline_unsafe(mem, _stack_pointer, _stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(ALLOCATE):
                _consume_instruction_operand_inline(mem, _instr_pointer, temp);
                _stack_pointer += temp;
                done();
                
            get_label(ADD):
                BINARY_OPERATION(+)
                _carry_borrow_flag = (word_type)((temp < operand_0) & (temp < operand_1));
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SUBTRACT):
                BINARY_OPERATION(-)
                _carry_borrow_flag = (word_type)((temp > operand_0) & (temp > operand_1));
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(MULTIPLY):
                BINARY_OPERATION(*)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(DIVIDE):
                BINARY_OPERATION(/)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(MOD):
                BINARY_OPERATION(%)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SHIFT_LEFT):
                BINARY_OPERATION(<<)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SHIFT_RIGHT):
                BINARY_OPERATION(>>)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(OR):
                BINARY_OPERATION(|)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(AND): BINARY_OPERATION(&)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(XOR):
                BINARY_OPERATION(^)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(ADD_FLOAT):
                FLOATING_BINARY_OPERATION(+)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SUBTRACT_FLOAT):
                FLOATING_BINARY_OPERATION(-)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(MULTIPLY_FLOAT):
                FLOATING_BINARY_OPERATION(*)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(DIVIDE_FLOAT):
                FLOATING_BINARY_OPERATION(/)
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(CONVERT_TO_FLOAT):
                operand_2 = _stack_pointer + 1;
                _translate_address_unsafe(mem, operand_2, operand_1);
                *(word_type *)operand_1 = float_as_word((float_type)(signed_word_type)*(word_type *)operand_1);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(CONVERT_TO_FLOAT_FROM_UNSIGNED):
                operand_2 = _stack_pointer + 1;
                _translate_address_unsafe(mem, operand_2, operand_1);
                *(word_type *)operand_1 = float_as_word((float_type)*(word_type *)operand_1);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(CONVERT_TO_INTEGER):
                operand_2 = _stack_pointer + 1;
                _translate_address_unsafe(mem, operand_2, operand_1);
                *(word_type *)operand_1 = word_as_float(*(word_type *)operand_1);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(NOT):
                operand_2 = _stack_pointer + 1;
                _translate_address_unsafe(mem, operand_2, operand_1);
                *(word_type *)operand_1 = ~*(word_type *)operand_1;
                UPDATE_INSTR_POINTER(_instr_pointer);
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
                _instr_pointer += (operand_0 ? operand_1 : 0);
                done();
                
            get_label(JUMP_FALSE):
                _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
                _consume_instruction_operand_inline(mem, _instr_pointer, operand_1);
                _instr_pointer += (operand_0 ? 0 : operand_1);
                done();
    
            get_label(JUMP_TABLE):
                #define number_of_values operand_0
                #define value operand_1
                #define median_value operand_2
    
                _consume_instruction_operand_inline(mem, _instr_pointer, number_of_values);
                temp = _instr_pointer;
                operand_3 = number_of_values;
    
                INCREMENT_POINTER(_instr_pointer);
                _pop_word_inline_unsafe(mem, _stack_pointer, value);
    
                while (number_of_values)
                {
                    __addr = _instr_pointer + (number_of_values >>= 1);  // number_of_values /= 2; cut the search space in half.
                    
                    check_median_value:
                        _get_word_inline_unsafe(mem, __addr,  median_value);
                        if (value == median_value)
                        {
                            __addr += operand_3;
                            _get_word_inline_unsafe(mem, __addr, _instr_pointer);
                            _instr_pointer += temp;
                            done();
                        }
                    
                    if (value > median_value && number_of_values)  // the value we are seeking is greater than the median and we still have values to work with ...
                    {
                        _instr_pointer = ++__addr;  // _instr_pointer += number_of_values-- + 1; value must be in greater half, remove the lower half ...
                        if (--number_of_values) // if we haven't removed all the values continue ...
                            continue ;
                        goto check_median_value; // all values have being removed, check that the current value is the one we are seeking...
                    }
                }
                _get_word_inline_unsafe(mem, temp, _instr_pointer); // value wasn't found so read default offset.
                _instr_pointer += temp;
                done();
                #undef number_of_values
                #undef value
                #undef median_value
                
            get_label(LOAD_ZERO_FLAG):
                LOAD_REGISTER(_zero_flag);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(LOAD_CARRY_BORROW_FLAG):
                LOAD_REGISTER(_carry_borrow_flag);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(LOAD_MOST_SIGNIFICANT_BIT_FLAG):
                LOAD_REGISTER(_msb_flag);
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(PUSH_FRAME):
                _new_frame(_temp_frame);
                set_frames_base_pointer(_temp_frame, _base_pointer);
                set_frames_stack_pointer(_temp_frame, _stack_pointer);
                set_next_frame(_temp_frame, _frames); // save the rest of the frames.
                _frames = _temp_frame; // add the frame
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(POP_FRAME):
                _base_pointer = frames_base_pointer(_frames);  // update base and stack pointer.
                _stack_pointer = frames_stack_pointer(_frames);
                
                _temp_frame = _frames; // save the frame for recycling.
                _frames = next_frame(_frames); // remove the frame
                
                set_next_frame(_temp_frame, recycle_frames);  // save the rest of the recycled fames.
                recycle_frames = _temp_frame;  // recycle frame.
                UPDATE_INSTR_POINTER(_instr_pointer);
                done();
                
            get_label(SYSTEM_CALL):
                _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
                _base_pointer += 3 * WORD_SIZE;
                #define _consume_parameter_inline(bs, mem, dest) _get_word_inline_unsafe(mem, bs, dest); INCREMENT_POINTER(bs)
  
                #define _set_str_inline(addr, dest, mem, char_buffer, max_length) {     \
                    _get_word_inline_unsafe(mem, addr, dest);                           \
                    while (max_length-- && (*char_buffer++ = dest))                     \
                        ++addr;                                                         \
                    --char_buffer;                                                      \
                }
                
                #define  _return_inline(value, mem, ip, bp, dest) { \
                    INCREMENT_POINTER(_base_pointer); /* assume that on return the frame will be popped updating _base_pointer */\
                    _get_word_inline_unsafe(mem, _base_pointer, _instr_pointer); /* returning to caller  */\
                    INCREMENT_POINTER(_base_pointer);    \
                    _get_word_inline_unsafe(mem, _base_pointer, dest); /* get location of return values storage */\
                    _set_word_inline_unsafe(mem, _base_pointer, dest, _base_pointer); /* actually returning the value */\
                }
                
                
                switch ((unsigned char)operand_0)
                {
                    default:
                        printf("Invalid System call " WORD_PRINTF_FORMAT "\n", operand_0);
                        goto end;
                        
                    case SYSTEM_CALL_ID(SYS_CALL_EXIT):
                        _move_word_inline_unsafe(mem, _base_pointer, (word_type)-1 * WORD_SIZE); // set exit status ...
                        _files = _opened_files;
                        while (_files) // flush all opened files ....
                        {
                            file = file_pointer(_files);
                            fflush(file); // flush the buffers but let os close the files.
                            _files = next_file_node(_files);
                        }
                        _base_pointer = _stack_pointer = (word_type)-1; // reset stack.
                        goto end;
                    
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
                        
                        _return_inline(file_id, mem, _instr_pointer, _base_pointer, operand_0);
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
                
            get_label(HALT):
                goto end;
                
            get_label(INVALID):
                printf("Invalid instruction!\n");
                goto end;
            
        goto execute_instruction;
    
    end:
        update_cpu(cpu); // update cpu state.
}
