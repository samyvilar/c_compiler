
#ifndef _KERNEL_H_
#define _KERNEL_H_

#include <stdio.h>
#include "word_type.h"
#include "sys_call_ids.h"

typedef struct file_node_type {
    struct file_node_type *next;
    word_type file_id;
    FILE *file_pointer;
} file_node_type;
#define next_file_node(file) (*(file_node_type **)(file))
#define set_next_file_node(file, value) (next_file_node(file) = (value))
#define file_id(file) ((file)->file_id)
#define set_file_id(file, value) (file_id(file) = (value))
#define file_pointer(file) ((file)->file_pointer)
#define set_file_pointer(file, value) (file_pointer(file) = (value))

struct kernel_type {
    void (*calls[256])(struct cpu_type *, struct virtual_memory_type *, struct kernel_type *);
    file_node_type *opened_files;
};
#define calls(kernel) (kernel->calls)
#define set_calls(kernel, values) memcpy(calls(kernel), (values), sizeof(calls(kernel)))
#define opened_files(kernel) ((kernel)->opened_files)
#define set_opened_files(kernel, values) (opened_files(kernel) = values)

#endif
