#include <stdio.h>

#include "fast_vm.h"
#include "cpu.h"
#include "kernel.h"

//const char *_instr_names_[] = {
//        [0 ... 255] = "INVALID INSTRUCTION",
//        [HALT] = "HALT",
//        [PASS] = "PASS",
//        [PUSH] = "PUSH",
//        [POP] = "POP",
//        [LOAD] = "LOAD",
//        [SET] = "SET",
//        [LOAD_BASE_STACK_POINTER] = "LOAD_BASE_STACK_POINTER",
//        [SET_BASE_STACK_POINTER] = "SET_BASE_STAC_POINTER",
//        [LOAD_STACK_POINTER] = "LOAD_STACK_POINTER",
//        [SET_STACK_POINTER] = "SET_STACK_POINTER",
//        [ALLOCATE] = "ALLOCATE",
//        [DUP] = "DUP",
//        [SWAP] = "SWAP",
//        [ADD] = "ADD",
//        [SUBTRACT] = "SUBTRACT",
//        [MULTIPLY] = "MULTIPLY",
//        [DIVIDE] = "DIVIDE",
//        [MOD] = "MOD",
//        [SHIFT_LEFT] = "SHIFT_LEFT",
//        [SHIFT_RIGHT] = "SHIFT_RIGHT",
//        [OR] = "OR",
//        [AND] = "AND",
//        [NOT] = "NOT",
//        [ADD_FLOAT] = "ADD_FLOAT",
//        [SUBTRACT_FLOAT] = "SUBTRACT_FLOAT",
//        [MULTIPLY_FLOAT] = "MULTIPLY_FLOAT",
//        [DIVIDE_FLOAT] = "DIVIDE_FLOAT",
//        [CONVERT_TO_FLOAT] = "CONVERT_TO_FLOAT",
//        [CONVERT_TO_INTEGER] = "CONVERT_TO_INTEGER",
//        [ABSOLUTE_JUMP] = "ABSOLUTE_JUMP",
//        [JUMP_FALSE] = "JUMP_FALSE",
//        [JUMP_TRUE] = "JUMP_TRUE",
//        [JUMP_TABLE] = "JUMP_TABLE",
//        [RELATIVE_JUMP] = "RELATIVE_JUMP",
//        [PUSH_FRAME] = "PUSH_FRAME",
//        [POP_FRAME] = "POP_FRAME",
//        [LOAD_ZERO_FLAG] = "LOAD_ZERO_FLAG",
//        [LOAD_CARRY_BORROW_FLAG] = "LOAD_CARRY_BORROW_FLAG",
//        [LOAD_MOST_SIGNIFICANT_BIT_FLAG] = "LOAD_MOST_SIGNIFICANT_BIT_FLAG",
//        [SYSTEM_CALL] = "SYSTEM_CALL"
//};


const word_type _instr_sizes_[256] = {INSTRUCTION_SIZES};

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
        /* get a recycled obj */                                    \
        (_dest_ptr = recycled),                                     \
        /*remove it from the list of available objs.*/              \
        (recycled = _next_obj(recycled));                           \
        else if (_available)                                        \
            /* get a new obj from the block.*/                      \
            _dest_ptr = (_block + --_available);                    \
        else                                                        \
        {                                                           \
            /* allocate new block ... */                            \
            _block = malloc(_quantity * sizeof(*_dest_ptr));        \
            /* remove one from the set*/                            \
            _available = _quantity - 1;                             \
            /* get the newly removed obj. */                        \
            _dest_ptr = (_block + _available);                      \
        }                                                           \
    }

#define _new_frame(_dest) _new(recycle_frames, frame_blocks, available_frames, _dest, next_frame, NUMBER_OF_FRAMES_PER_BLOCK)
#define _new_file_node(_dest) _new(recycle_file_nodes, file_nodes_block, available_file_nodes, _dest, next_file_node, NUMBER_OF_FILE_NODES_PER_BLOCK)

#define _file_node_inline(_files, _file_id) {               \
    while (_files && (file_id(_files) != _file_id))         \
        _files = next_file_node(_files);                    \
    }


INLINE_FUNC_SIGNATURE(evaluate) {
    /* x86 has 8 (so call) general purpose registers, x86_64 doubles that to 16 ...*/
    /* x86 (RAX, RBX, RCX, RDX) index (RSI (source), RDI (destination), RBP (base pointer), RSP (stack pointer)) */
    /* x86_64 (R8-R15) and SSE (XMM0 - XMM15) 128 bit registers (should be quite common today) */
    /* CPU State ... */

    register word_type
        _stack_pointer = stack_pointer(cpu),
        _instr_pointer = instr_pointer(cpu);
    
    register word_type
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
    
    #define _pop_word(mem, sp) get_word(mem, ++sp)
    #define _push_word(mem, sp, value) set_word(mem, sp--, value)
    #define _operand(ip, mem, index) get_word(mem, ip + WORD_SIZE + index)

    /* Virtual Memory address translation variables ... */
    register word_type
        _hash,
        _addr;

    register void *_temp;

    #define _translate_address_unsafe(mem, addr, dest) \
        TRANSLATE_ADDRESS_INLINE(mem, addr, dest, _hash, _temp)

    
    #define _translate_address(mem, addr, dest) _addr = (addr); _translate_address_unsafe(mem, _addr, dest)
    
    #define __get_word_inline__(_trans_adr, mem, addr, dest) _trans_adr(mem, addr, dest) dest = *(word_type *)dest
    
    #define _get_word_inline(mem, addr, dest) __get_word_inline__(_translate_address, mem, addr, dest)
    #define _get_word_inline_unsafe(mem, addr, dest) __get_word_inline__(_translate_address_unsafe, mem, addr, dest)
    
    #define __set_word_inline__(_trans_adr, mem, addr, value, dest) _trans_adr(mem, addr, dest) *(word_type *)dest = value
    #define _set_word_inline(mem, addr, value, dest) __set_word_inline__(_translate_address, mem, addr, value, dest)
    #define _set_word_inline_unsafe(mem, addr, value, dest) __set_word_inline__(_translate_address_unsafe, mem, addr, value, dest)
    
    #define _operand_inline(ip, mem, index, dest) _get_word_inline(mem, ip + WORD_SIZE + index, dest)
    
    #define _pop_word_inline(mem, sp, dest) _get_word_inline(mem, ++sp, dest)   
    #define _pop_word_inline_unsafe(mem, sp, dest) ++sp; _get_word_inline_unsafe(mem, sp, dest)
    
    #define _push_word_inline(mem, sp, value, dest) _set_word_inline(mem, sp--, value, dest)
    #define _push_word_inline_unsafe(mem, sp, value, dest) _set_word_inline_unsafe(mem, sp, value, dest); sp--
    
    #define _move_word_inline_unsafe(mem, src, dest)        \
        _translate_address_unsafe(mem, src, temp)           \
        _translate_address_unsafe(mem, dest, operand_3)     \
        *(word_type *)operand_3 = *(word_type *)temp
    
    #define _swap_word_inline_unsafe(mem, src_0, src_1)     \
        _translate_address_unsafe(mem, src_0, temp);        \
        _translate_address_unsafe(mem, src_1, operand_3);   \
        _addr = *(word_type *)temp;                         \
        *(word_type *)temp = *(word_type *)operand_3;       \
        *(word_type *)operand_3 = _addr


    #define INCREMENT_POINTER(value) (++value)
    #define DECREMENT_POINTER(value) (--value)
    #define INCREMENT_POINTER_TWICE(value) (value += 2 * WORD_SIZE)

    #define UPDATE_INSTR_POINTER(_ip) ++_ip
    #define UPDATE_INSTR_POINTER_WIDE(_ip) UPDATE_INSTR_POINTER(_ip); UPDATE_INSTR_POINTER(_ip)


    #define _BINARY_OPERATION(_o_, oper_0, oper_1, result, conv_from_word, conv_to_word, msb_func) \
            _pop_word_inline(mem, _stack_pointer, oper_1); /*oper_1 = conv_from_word(_pop_word(mem, _stack_pointer));*/\
            _pop_word_inline(mem, _stack_pointer, oper_0); /*oper_0 = conv_from_word(_pop_word(mem, _stack_pointer));*/ \
            result = oper_0 _o_ oper_1;   \
            _push_word_inline(mem, _stack_pointer, result, operand_2); /*_push_word(mem, _stack_pointer, conv_to_word(result));*/\
            _zero_flag = !result; \
            _msb_flag = msb_func(result);

    #define BINARY_OPERATION(_o_)  _BINARY_OPERATION(_o_, operand_0, operand_1, temp, , , MSB)

    /*
    #define BINARY_OPERATION(_o_) \
            operand_1 = _pop_word(mem, _stack_pointer); \
            operand_0 = get_word(mem, (_stack_pointer + WORD_SIZE)); \
            temp = operand_0 _o_ operand_1;   \
            set_word(mem, (_stack_pointer + WORD_SIZE), temp); \
            _zero_flag = !temp; \
            _msb_flag = MSB(temp);
    */
    #define LESS_THAN_ZERO(value) ((value) < 0.0)
    #define FLOATING_BINARY_OPERATION(_o_) \
        _pop_word_inline(mem, _stack_pointer, operand_1); \
        float_operand_1 = word_as_float(operand_1); \
        _pop_word_inline(mem, _stack_pointer, operand_0); \
        float_operand_0 = word_as_float(operand_0); \
        float_temp = float_operand_0 _o_ float_operand_1;   \
        temp = float_as_word(float_temp); \
        _push_word_inline(mem, _stack_pointer, temp, operand_2); /*_push_word(mem, _stack_pointer, conv_to_word(result));*/\
        _zero_flag = !float_temp; \
        _msb_flag = float_temp < 0.0;
    /*
        _BINARY_OPERATION( \
            _o_, \
            float_operand_0, \
            float_operand_1, \
            float_temp, \
            word_as_float, \
            float_as_word, \
            LESS_THAN_ZERO \
        )
     */
    /*
    #define FLOATING_BINARY_OPERATION(_o_) \
        float_operand_1 = word_as_float(_pop_word(mem, _stack_pointer)); \
        float_operand_0 = word_as_float(get_word(mem, (_stack_pointer + WORD_SIZE))); \
        float_temp = float_operand_0 _o_ float_operand_1; \
        set_word(mem, (_stack_pointer + WORD_SIZE), float_as_word(float_temp)); \
        _zero_flag = !float_temp; \
        _msb_flag = float_temp < 0.0;
    */

    #define update_cpu(cpu) \
        set_base_pointer(cpu, _base_pointer);   \
        set_stack_pointer(cpu, _stack_pointer); \
        set_instr_pointer(cpu, _instr_pointer); \
        set_zero_flag(cpu, _zero_flag);         \
        set_carry_borrow_flag(cpu, _carry_borrow_flag); \
        set_most_significant_bit_flag(cpu, _msb_flag);  \
        set_frames(cpu, _frames);

    #define cache_cpu(cpu)  \
        _base_pointer = base_pointer(cpu);              \
        _stack_pointer = stack_pointer(cpu);            \
        _instr_pointer = instr_pointer(cpu);            \
        _zero_flag = zero_flag(cpu);                    \
        _carry_borrow_flag = carry_borrow_flag(cpu);    \
        _msb_flag = most_significant_bit_flag(cpu);     \
        _frames = frames(cpu);

    #define _consume_instruction_operand_inline(mem, _instr_pointer, _operand)  \
        UPDATE_INSTR_POINTER(_instr_pointer);                                   \
        _get_word_inline_unsafe(mem, _instr_pointer, _operand);                 \
        UPDATE_INSTR_POINTER(_instr_pointer);
    
    register unsigned char _current_instr;
    
    while (1) {
        _get_word_inline_unsafe(mem, _instr_pointer, temp);
        _current_instr = (temp & 255);
        switch (temp)
        {
            case INSTR_ID(PASS):
                INCREMENT_POINTER(_instr_pointer);
                break;

            case INSTR_ID(PUSH):
                //_operand_inline(_instr_pointer, mem, 0, operand_0);
                //_push_word_inline(mem, _stack_pointer, operand_0, temp);
                UPDATE_INSTR_POINTER(_instr_pointer);
                _move_word_inline_unsafe(mem, _instr_pointer, _stack_pointer);
                DECREMENT_POINTER(_stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(POP):
                INCREMENT_POINTER(_stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            #define number_of_elements operand_0
            #define src_address operand_1
            #define dest_address operand_2
            case INSTR_ID(LOAD):
                // number_of_elements = _operand(_instr_pointer, mem, 0); // number of bytes
                // _operand_inline(_instr_pointer, mem, 0, number_of_elements);
                _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
                
                // src_address = number_of_elements + _pop_word(mem, _stack_pointer); // src address
                _pop_word_inline_unsafe(mem, _stack_pointer, src_address);
                src_address += number_of_elements;
                
                while (number_of_elements--)
                {
                    //_push_word(mem, _stack_pointer, get_word(mem, --src_address));  // loading in reverse order ...

                    // _get_word_inline(mem, --src_address, temp);
                    // _push_word_inline(mem, _stack_pointer, temp, dest_address);
                    
                    DECREMENT_POINTER(src_address);
                    _move_word_inline_unsafe(mem, src_address, _stack_pointer);
                    DECREMENT_POINTER(_stack_pointer);
                }
                
                // UPDATE_INSTR_POINTER_WIDE(_instr_pointer);
                break ;

            case INSTR_ID(SET):
                // number_of_elements = _operand(_instr_pointer, mem, 0); // number of bytes
                //_operand_inline(_instr_pointer, mem, 0, number_of_elements);
                _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
                
                // dest_address = _pop_word(mem, _stack_pointer); // destination address
                _pop_word_inline_unsafe(mem, _stack_pointer, dest_address);
                
                src_address = _stack_pointer;
                while (number_of_elements--)
                {
                    // set_word(mem, dest_address++, get_word(mem, ++src_address));
                    
                    // _get_word_inline(mem, ++src_address, temp);
                    // _set_word_inline(mem, dest_address++, temp, operand_3);
                    
                    INCREMENT_POINTER(src_address);
                    _move_word_inline_unsafe(mem, src_address, dest_address);
                    INCREMENT_POINTER(dest_address);
                }
                
                // UPDATE_INSTR_POINTER_WIDE(_instr_pointer);
                break ;

            case INSTR_ID(DUP):
                // number_of_elements = _operand(_instr_pointer, mem, 0); // number of elements.
                // _operand_inline(_instr_pointer, mem, 0, number_of_elements);
                
                _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
                src_address = _stack_pointer + operand_0; // src
                
                while (number_of_elements--)
                {
                    // _push_word(mem, _stack_pointer, get_word(mem, src_address--));
                    
                    // _get_word_inline(mem, src_address--, temp);
                    // _push_word_inline(mem, _stack_pointer, temp, operand_2);
                    
                    _move_word_inline_unsafe(mem, src_address, _stack_pointer);
                    DECREMENT_POINTER(src_address);
                    DECREMENT_POINTER(_stack_pointer);
                }
                // UPDATE_INSTR_POINTER_WIDE(_instr_pointer);
                break ;

            case INSTR_ID(SWAP):
                // number_of_elements = _operand(_instr_pointer, mem, 0); // number of elements
                // _operand_inline(_instr_pointer, mem, 0, number_of_elements);
                
                _consume_instruction_operand_inline(mem, _instr_pointer, number_of_elements);
                src_address = _stack_pointer + number_of_elements; // offset
                dest_address = src_address + number_of_elements; // other values ...

                while (number_of_elements--)
                {
//                    temp = get_word(mem, src_address);        // method_1
//                    set_word(mem, src_address--, get_word(mem, operand_2));
//                    set_word(mem, operand_2--, temp);
                    
//                    #define value_0 temp // method_2
//                    #define value_1 operand_2
//                    // get values
//                    _get_word_inline(mem, src_address, value_0);
//                    _get_word_inline(mem, (src_address + number_of_elements), value_1);
//                    
//                    // swap values
//                    _set_word_inline(mem, src_address, value_1, operand_3);
//                    _set_word_inline(mem, (src_address + number_of_elements), value_0, operand_3);
//                    --src_address;
//                    @@--number_of_elements;
                    
                    _swap_word_inline_unsafe(mem, src_address, dest_address); // method_3
                    DECREMENT_POINTER(src_address);
                    DECREMENT_POINTER(dest_address);
                }
                // UPDATE_INSTR_POINTER_WIDE(_instr_pointer);
                break ;
                
            #undef number_of_elements
            #undef src_address
            #undef dest_address

            #define LOAD_REGISTER(reg) _push_word_inline_unsafe(mem, _stack_pointer, reg, temp)
            #define SET_REGISTER(reg) _pop_word_inline_unsafe(mem, _stack_pointer, reg)
            case INSTR_ID(LOAD_BASE_STACK_POINTER):
                // _push_word(mem, _stack_pointer, _base_pointer);
                LOAD_REGISTER(_base_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SET_BASE_STACK_POINTER):
                // _base_pointer = _pop_word(mem, _stack_pointer);
                // _pop_word_inline(mem, _stack_pointer, _base_pointer);
                SET_REGISTER(_base_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(LOAD_STACK_POINTER):
                // set_word(mem, _stack_pointer, _stack_pointer);
                _set_word_inline_unsafe(mem, _stack_pointer, _stack_pointer, temp);
                DECREMENT_POINTER(_stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SET_STACK_POINTER):
                // _stack_pointer = get_word(mem, (_stack_pointer + WORD_SIZE));
                INCREMENT_POINTER(_stack_pointer);
                _get_word_inline_unsafe(mem, _stack_pointer, _stack_pointer);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(ALLOCATE):
                // _stack_pointer += _operand(_instr_pointer, mem, 0);
                // _operand_inline(_instr_pointer, mem, 0, temp);
                _consume_instruction_operand_inline(mem, _instr_pointer, temp);
                _stack_pointer += temp;
                // UPDATE_INSTR_POINTER_WIDE(_instr_pointer);
                break ;

            case INSTR_ID(ADD):
                BINARY_OPERATION(+)
                _carry_borrow_flag = (word_type)((temp < operand_0) & (temp < operand_1));
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SUBTRACT):
                BINARY_OPERATION(-)
                _carry_borrow_flag = (word_type)((temp > operand_0) & (temp > operand_1));
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(MULTIPLY):
                BINARY_OPERATION(*)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(DIVIDE):
                BINARY_OPERATION(/)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(MOD):
                BINARY_OPERATION(%)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SHIFT_LEFT):
                BINARY_OPERATION(<<)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SHIFT_RIGHT):
                BINARY_OPERATION(>>)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(OR):
                BINARY_OPERATION(|)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(AND): BINARY_OPERATION(&)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(XOR):
                BINARY_OPERATION(^)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(ADD_FLOAT):
                FLOATING_BINARY_OPERATION(+)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SUBTRACT_FLOAT):
                FLOATING_BINARY_OPERATION(-)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(MULTIPLY_FLOAT):
                FLOATING_BINARY_OPERATION(*)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(DIVIDE_FLOAT):
                FLOATING_BINARY_OPERATION(/)
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;
                
            case INSTR_ID(CONVERT_TO_FLOAT):
                // float_temp = (float_type)(signed_word_type)_pop_word(mem, _stack_pointer);
                _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
                operand_0 = float_as_word((float_type)(signed_word_type)operand_0);
                //_push_word(mem, _stack_pointer, float_as_word(float_temp));
                _push_word_inline_unsafe(mem, _stack_pointer, operand_0, temp);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(CONVERT_TO_FLOAT_FROM_UNSIGNED):
                // float_temp = (float_type)_pop_word(mem, _stack_pointer);
                _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
                operand_0 = float_as_word((float_type)operand_0);
                // _push_word(mem, _stack_pointer, float_as_word(float_temp));
                _push_word_inline_unsafe(mem, _stack_pointer, operand_0, temp);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(CONVERT_TO_INTEGER):
                // operand_0 = _pop_word(mem, _stack_pointer);
                _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
                // _push_word(mem, _stack_pointer, word_as_float(operand_0));
                _push_word_inline_unsafe(mem, _stack_pointer, word_as_float(operand_0), temp);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(NOT):
                // operand_0 = _pop_word(mem, _stack_pointer);
                _pop_word_inline_unsafe(mem, _stack_pointer, operand_0);
                // _push_word(mem, _stack_pointer, ~operand_0);
                operand_0 = ~operand_0;
                _push_word_inline_unsafe(mem, _stack_pointer, operand_0, temp);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(ABSOLUTE_JUMP):
                // _instr_pointer = _pop_word(mem, _stack_pointer);
                _pop_word_inline(mem, _stack_pointer, _instr_pointer);
                break ;
                
            case INSTR_ID(RELATIVE_JUMP):
                //_instr_pointer += _operand(_instr_pointer, mem, 0);
                // _operand_inline(_instr_pointer, mem, 0, operand_0);
                _consume_instruction_operand_inline(mem, _instr_pointer, operand_0);
                _instr_pointer += operand_0;
                break ;

            case INSTR_ID(JUMP_TRUE):
                // _instr_pointer += (_pop_word(mem, _stack_pointer) ? _operand(_instr_pointer, mem, 0) : (2 * WORD_SIZE));
                //_instr_pointer += (!!_pop_word(mem, _stack_pointer) * (_operand(_instr_pointer, mem, 0) - (2 * WORD_SIZE))) + (2 * WORD_SIZE);
                _pop_word_inline(mem, _stack_pointer, operand_0);
                _consume_instruction_operand_inline(mem, _instr_pointer, operand_1);
                _instr_pointer += (!!operand_0 * operand_1);
                
                break ;

            case INSTR_ID(JUMP_FALSE):
                // _instr_pointer += (_pop_word(mem, _stack_pointer) ? (2 * WORD_SIZE) : _operand(_instr_pointer, mem, 0));
                // _instr_pointer += (!_pop_word(mem, _stack_pointer) * (_operand(_instr_pointer, mem, 0) - (2 * WORD_SIZE))) + (2 * WORD_SIZE);
                _pop_word_inline(mem, _stack_pointer, operand_0);
                _consume_instruction_operand_inline(mem, _instr_pointer, operand_1);
                _instr_pointer += (!operand_0 * operand_1);
                break ;

            case INSTR_ID(JUMP_TABLE):
                #define number_of_values operand_0
                #define value operand_1
                #define median_value operand_2
                #define default_offset operand_3
                #define base _instr_pointer
                
                // number_of_values = _operand(_instr_pointer, mem, 0); // number of cases ...
                // _operand_inline(_instr_pointer, mem, 0, number_of_values);
                
                _consume_instruction_operand_inline(mem, base, number_of_values);
                temp = _instr_pointer;{{
                _get_word_inline_unsafe(mem, base, default_offset);
                INCREMENT_POINTER(base);
                
                // value = _pop_word(mem, _stack_pointer); // value to look for
                _pop_word_inline_unsafe(mem, _stack_pointer, value);
                
                // base = _instr_pointer + (3 * WORD_SIZE); // Skip JumpTable, number of values, default addr ...

                //  operand_2 = _operand(_instr_pointer, mem, 1); // default address if none found.
                // Assume that all values are ordered, if so, apply binary search ...
                while (number_of_values)
                {   // in case of odd number of cases, values are always at an even offset.
                    // median_value = get_word(mem, (base + (number_of_values -= (number_of_values % 2))));
                    
                    _get_word_inline(mem, (base + (number_of_values -= (number_of_values % 2))), median_value);
                    
                    if (value == median_value)
                    {
                        // _instr_pointer += get_word(mem, (base + number_of_values + WORD_SIZE));
                        base += number_of_values;
                        ++base;
                        _get_word_inline_unsafe(mem, base, default_offset);  // 'value' wont be read again.
                        break;
                    }

                    if (value > median_value)  // the value we are seeking is greater than the median ...
                        base += number_of_values + (2 * WORD_SIZE); // value must be in greater half, remove the lower half ...

                    number_of_values >>= 1; // number_of_values /= 2; cut the search space in half.
                }
                // _instr_pointer += _operand(_instr_pointer, mem, 1);  // value wasn't found just jump to default ...
                _instr_pointer = temp + default_offset;

//                while (operand_0--)
//                {
//                    if (operand_1 == get_word(mem, temp))
//                    {
//                        operand_2 = get_word(mem, (temp + WORD_SIZE));
//                        break ;
//                    }
//                    temp += 2 * WORD_SIZE;
//                }
//                _instr_pointer += operand_2;
                #undef number_of_values
                #undef value
                #undef median_value
                #undef base
                // _addr_found:
                break ;
                
            case INSTR_ID(LOAD_ZERO_FLAG):
                // _push_word(mem, _stack_pointer, _zero_flag);
                LOAD_REGISTER(_zero_flag);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(LOAD_CARRY_BORROW_FLAG):
                // _push_word(mem, _stack_pointer, _carry_borrow_flag);
                LOAD_REGISTER(_carry_borrow_flag);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(LOAD_MOST_SIGNIFICANT_BIT_FLAG):
                // _push_word(mem, _stack_pointer, _msb_flag);
                LOAD_REGISTER(_msb_flag);
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;
                

            case INSTR_ID(PUSH_FRAME):
//                if (recycle_frames)
//                    (_temp_frame = recycle_frames), // get a recycled frame
//                    (recycle_frames = next_frame(recycle_frames)); // remove it from the list of available frames.
//                else if (available_frames)
//                    _temp_frame = (frame_blocks + --available_frames);  // get an allocated new frame from the block.
//                else
//                {
//                    frame_blocks = malloc(NUMBER_OF_FRAMES_PER_BLOCK * sizeof(frame_type));  // allocate new set of frames.
//                    available_frames = NUMBER_OF_FRAMES_PER_BLOCK - 1; // remove one from the set
//                    _temp_frame = (frame_blocks + available_frames); // get the newly removed frame.
//                }
                
                _new_frame(_temp_frame);
                // save the base and stack pointer in the frame object.
                set_frames_base_pointer(_temp_frame, _base_pointer);
                set_frames_stack_pointer(_temp_frame, _stack_pointer);
                set_next_frame(_temp_frame, _frames); // save the rest of the frames.
                _frames = _temp_frame; // add the frame
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(POP_FRAME):
                _base_pointer = frames_base_pointer(_frames);  // update base and stack pointer.
                _stack_pointer = frames_stack_pointer(_frames);

                _temp_frame = _frames; // save the frame for recycling.
                _frames = next_frame(_frames); // remove the frame

                set_next_frame(_temp_frame, recycle_frames);  // save the rest of the recycled fames.
                recycle_frames = _temp_frame;  // recycle frame.
                UPDATE_INSTR_POINTER(_instr_pointer);
                break ;

            case INSTR_ID(SYSTEM_CALL):
                _pop_word_inline(mem, _stack_pointer, operand_0);
                #define _parameter_inline(bs, mem, index, dest) _get_word_inline(mem, bs + (3 * WORD_SIZE) + index, dest)
                #define _set_str_inline(addr, dest, mem, char_buffer, max_length) {     \
                    _get_word_inline(mem, addr, dest);                                  \
                    while (max_length-- && (*char_buffer++ = dest))                     \
                        ++addr;                                                         \
                    --char_buffer;                                                      \
                }
                
                #define  _return_inline(value, mem, ip, bp, dest) { \
                    ++_base_pointer; /* assume that on return the frame will be popped updating _base_pointer */\
                    _get_word_inline(mem, _base_pointer, _instr_pointer); /* returning to caller  */\
                    ++_base_pointer;    \
                    _get_word_inline(mem, _base_pointer, dest); /* get location of return values storage */\
                    _set_word_inline(mem, _base_pointer, dest, _base_pointer); /* actually returning the value */\
                }


                switch ((unsigned char)operand_0)
                {
                    default:
                        printf("Invalid System call " WORD_PRINTF_FORMAT "\n", operand_0);
                        goto end;
                        
                    case SYSTEM_CALL_ID(SYS_CALL_EXIT):
                        _base_pointer += 3 * WORD_SIZE;
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
                        _parameter_inline(_base_pointer, mem, 0, file_path_ptr);
                        _parameter_inline(_base_pointer, mem, 1, mode_ptr);
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
                        _parameter_inline(_base_pointer, mem, 0, _file_id);
                        _parameter_inline(_base_pointer, mem, 1, buffer_ptr);
                        _parameter_inline(_base_pointer, mem, 2, number_of_bytes);
                            
                        _files = _opened_files;
                        _file_node_inline(_files, _file_id);
                        
                        if (_files)
                        {
                            file = file_pointer(_files);
                            while (number_of_bytes-- && !ferror(file))
                            {
                                _get_word_inline(mem, buffer_ptr++, temp);
                                fputc((int)temp, file);
                            }
                            _file_id = (word_type)ferror(file);
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
                break ;
                

            case INSTR_ID(HALT):
                goto end;

            default:
                printf("Invalid instruction!\n");
                goto end;
        }
    }

    end:
        update_cpu(cpu); // update cpu state.
}
