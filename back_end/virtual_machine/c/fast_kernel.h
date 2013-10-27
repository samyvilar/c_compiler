//
//  fast_kernel.h
//  virtual_machine
//
//  Created by Samy Vilar on 10/4/13.
//
//

#ifndef _FAST_KERNEL_H_
#define _FAST_KERNEL_H_

#include "kernel.h"


#define _parameter_inline(index, _base_pointer, dest) _get_word_inline(mem, _base_pointer + (3 * WORD_SIZE) + index, dest)

#define EXIT_SYS_CALL(operand_0, _base_pointer, _opened_files) {        \
    while (files)                                                       \
    {                                                                   \
        fflush(file_pointer(files));                                    \
        if (file_id(files) != SYS_STD_IN && file_id(files) != SYS_STD_OUT && file_id(files) != SYS_STD_ERROR)   \
            fclose(file_pointer(files));                                \
        files = next(files);                                            \
    }                                                                   \
    set_word(mem, (word_type)-1, exit_status);
set_stack_pointer(cpu, -1);  // reset the stack
set_base_pointer(cpu, -1);
set_word(mem, instr_pointer(cpu), HALT); // update next instruction so machine halts ...


#define OPEN_SYS_CALL()
#define READ_SYS_CALL()
#define WRITE_SYS_CALL()
#define CLOSE_SYS_CALL()
#define TELL_SYS_CALL()
#define SEEK_SYS_CALL()
#define INVALID_SYS_CALL()

#define CALLS(call_id, mem, _instr_pointer, _base_pointer)  \
switch ((unsigned char)call_id) {                       \
case (unsigned char)SYS_EXT:  EXIT_SYS_CALL(); break ;              \
case (unsigned char)SYS_CALL_OPEN: OPEN_SYS_CALL(); break ;         \
case (unsigned char)SYS_CALL_READ: READ_SYS_CALL(); break ;         \
case (unsigned char)SYS_CALL_WRITE: WRITE_SYS_CALL(); break ;       \
case (unsigned char)SYS_CALL_CLOSE: CLOSE_SYS_CALL(); break ;       \
case (unsigned char)SYS_CALL_TELL: TELL_SYS_CALL(); break ;         \
case (unsigned char)SYS_CALL_SEEK: SEEK_SYS_CALL(); break ;         \
default: INVALID_SYS_CALL(); break ;                                \
}



#endif
