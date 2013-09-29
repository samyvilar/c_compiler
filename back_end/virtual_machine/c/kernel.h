
#ifndef _KERNEL_H_
#define _KERNEL_H_

#include "virtual_memory.h"
#include "cpu.h"
#include <stdio.h>

#define SYS_CALL_OPEN 5
#define SYS_CALL_READ 3
#define SYS_CALL_WRITE 4
#define SYS_CALL_CLOSE 6
#define SYS_CALL_TELL 198
#define SYS_CALL_SEEK 199
#define SYS_CALL_EXIT 1

#define SYS_STD_IN 0
#define SYS_STD_OUT 1
#define SYS_STD_ERROR 2

typedef struct file_node_type {
    struct file_node_type *next;
    word_type file_id;
    FILE *file_pointer;
} file_node_type;
#define next(file) (*(file_node_type **)(file))
#define set_next(file, value) (next(file) = (value))
#define file_id(file) ((file)->file_id)
#define set_file_id(file, value) (file_id(file) = (value))
#define file_pointer(file) ((file)->file_pointer)
#define set_file_pointer(file, value) (file_pointer(file) = (value))

struct kernel_type {
    void (*calls[256])(cpu_type *, virtual_memory_type *, struct kernel_type *);
    file_node_type *opened_files;
};
#define calls(kernel) (kernel->calls)
#define set_calls(kernel, values) memcpy(calls(kernel), (values), sizeof(calls(kernel)))
#define opened_files(kernel) ((kernel)->opened_files)
#define set_opened_files(kernel, values) (opened_files(kernel) = values)

#endif