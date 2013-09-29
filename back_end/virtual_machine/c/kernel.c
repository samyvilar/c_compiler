#include <stdio.h>
#include "kernel.h"

#define parameter(index, cpu, mem) get_word(mem, base_pointer(cpu) + 3 + index)

INLINE file_node_type *file_node(file_node_type *opened_files, word_type file_id, virtual_memory_type *mem)
{
    while (opened_files && file_id(opened_files) != file_id)
        opened_files = next(opened_files);
    return opened_files;
}


INLINE int is_file_opened(file_node_type *opened_files, word_type file_id, virtual_memory_type *mem)
{
    while (opened_files && file_id(opened_files) != file_id)
        opened_files = next(opened_files);
    return opened_files ? file_id(opened_files) == file_id : 0;
}

INLINE file_node_type *new_file_node(virtual_memory_type *mem, word_type file_id, FILE *file_pointer, file_node_type *next)
{
    file_node_type *new_file = malloc(sizeof(file_node_type)); // TODO:
    set_file_id(new_file, file_id);
    set_file_pointer(new_file, file_pointer);
    set_next(new_file, next);
    return new_file;
}


#define free_file_node free

INLINE file_node_type *remove_file(file_node_type *opened_files, word_type file_id, virtual_memory_type *mem)
{   // assumes that the file_id is withing the link list and isn't the first node ...
    // return pointer to removed node ...
    file_node_type *node;
    while (file_id(next(opened_files)) != file_id)  // search for the previous file ...
        opened_files = next(opened_files);
    set_next(opened_files, next((node = next(opened_files))));
    return node;
}


static INLINE char *set_str(word_type addr, virtual_memory_type *mem, char *buffer, word_type max_length)
{
    while (max_length-- && (*buffer++ = (char)get_word(mem, addr)))
        ++addr;
    return --buffer; // return pointer to the last set byte this should be '\0' unless we hit max_length ...
}
//static INLINE char *set_buffer(word_type addr, virtual_memory_type *mem, char *buffer, word_type max_length, word_type quantity)
//{
//    while (quantity-- && max_length--)  //stop when we've either filled the buffer or read all the characters ...
//        (*buffer++ = (char)get_word(mem, addr)), ++addr;
//    return buffer; // return address to last unfilled element, diff should equal quantity unless we hit max_length ...
//}


INLINE void _return_(word_type value, cpu_type *cpu, virtual_memory_type *mem)
{
    // set return value ...
    set_word(mem, get_word(mem, base_pointer(cpu) + 2), value);
    // load return address and update instruction pointer ...
    set_instr_pointer(cpu, get_word(mem, base_pointer(cpu) + 1));
}

INLINE_FUNC_SIGNATURE(__invalid_system_call__) {
    printf("Invalid System Call!\n");
    _return_((word_type)-1, cpu, mem);
}
INLINE_FUNC_SIGNATURE(__open__) {
    // int __open__(const char * file_path, const char *mode);
    // returns file_id on success or -1 of failure.
    word_type
            file_path_ptr = parameter(0, cpu, mem),
            mode_ptr = parameter(1, cpu, mem),
            file_id = (word_type)-1;

    char file_path[1024], mode[10];
    if (*set_str(file_path_ptr, mem, file_path, 1024))
    {
        printf("File Name exceeds 1024 characters ... \n");
        _return_((word_type)-1, cpu, mem);
        return ;
    }
    if (*set_str(mode_ptr, mem, mode, 10))
    {
        printf("File Mode exceeds 10 characters ...\n");
        _return_((word_type)-1, cpu, mem);
        return ;
    }

    FILE *file = fopen(file_path, mode);
    if (file)
        set_opened_files(os, new_file_node(mem, (file_id = (word_type)fileno(file)), file, opened_files(os)));
    else
        printf("Failed to opened file %s\n", file_path);

    _return_(file_id, cpu, mem);
}

INLINE_FUNC_SIGNATURE(__close__) {
    // int __close__(int);  // returns 0 on success or -1 on failure
    // returns 0 on success or -1 on failure.
    word_type file_id = parameter(0, cpu, mem);
    if (is_file_opened(opened_files(os), file_id, mem))
    {
        if (file_id == SYS_STD_OUT || file_id == SYS_STD_IN || file_id == SYS_STD_ERROR)
            (file_id = 0), fflush(stdout), fflush(stderr); // don't close but do flush ...
        else
        {
            file_node_type *node;
            if (file_id(opened_files(os)) == file_id)  // if removing last added file just update
                set_opened_files(os, next(next((node = opened_files(os)))));
            else  // file has being opened but isn't the initial, so safe to call remove_file ...
                node = remove_file(opened_files(os), file_id, mem);
            fflush(file_pointer(node));
            free_file_node(node);
            file_id = 0;
        }
    }
    else
        file_id = (word_type)-1;
    _return_(file_id, cpu, mem);
}


INLINE_FUNC_SIGNATURE(__read__) {
    // int __read__(int file_id, char *dest, unsigned long long number_of_bytes);
    // returns the number of elements read on success or -1 on failure
    word_type
            file_id = parameter(0, cpu, mem),
            dest_ptr = parameter(1, cpu, mem),
            number_of_bytes = parameter(2, cpu, mem);

    file_node_type *file = file_node(opened_files(os), file_id, mem);
    if (file)
    {
        word_type total_request_bytes = number_of_bytes;
        while (number_of_bytes-- && set_word(mem, dest_ptr, getc(file_pointer(file))) != EOF)
            ++dest_ptr;
        number_of_bytes = (get_word(mem, dest_ptr) == EOF) ? (word_type)-1 : (total_request_bytes - number_of_bytes);
    }
    else
        number_of_bytes = (word_type)-1;
    _return_(number_of_bytes, cpu, mem);
}

INLINE_FUNC_SIGNATURE(__write__) {
    //int  __write__(int file_id, char *buffer, unsigned long long number_of_bytes);
    // returns 0 on success or -1 on failure.
    word_type
            file_id = parameter(0, cpu, mem),
            buffer_ptr = parameter(1, cpu, mem),
            number_of_bytes = parameter(2, cpu, mem);

    file_node_type *file = file_node(opened_files(os), file_id, mem);

    if (file)
    {
        while (number_of_bytes-- && !ferror(file_pointer(file)))
            fputc((int)get_word(mem, buffer_ptr), file_pointer(file)), ++buffer_ptr;

        file_id = (word_type)ferror(file_pointer(file));
        fflush(file_pointer(file));
    }
    else
    {
        file_id = (word_type)-1;  // the file has yet to be opened ...
        printf("error file not open!\n");
    }
    _return_(file_id, cpu, mem);
}

INLINE_FUNC_SIGNATURE(__tell__) {
    // long int __tell__(int);
    word_type file_id = parameter(0, cpu, mem);
    file_node_type *file = file_node(opened_files(os), file_id, mem);

    _return_((file ? (word_type)ftell(file_pointer(file)) : (word_type)-1), cpu, mem);
}

INLINE_FUNC_SIGNATURE(__seek__) {
    // int __seek__(int file_id, int offset, int whence);
    word_type
            file_id = parameter(0, cpu, mem),
            offset = parameter(1, cpu, mem),
            whence = parameter(2, cpu, mem);
    file_node_type *file = file_node(opened_files(os), file_id, mem);

    _return_((file ? (word_type)fseek(file_pointer(file), (long)offset, (int)whence) : (word_type)-1), cpu, mem);
}

INLINE_FUNC_SIGNATURE(__exit__) {
    word_type exit_status = parameter(0, cpu, mem);
    file_node_type *files = opened_files(os);

    while (files)
    {
        fflush(file_pointer(files));
        // close all non std opened files ...
        if (file_id(files) != SYS_STD_IN && file_id(files) != SYS_STD_OUT && file_id(files) != SYS_STD_ERROR)
            fclose(file_pointer(files));
        files = next(files);
    }
    set_word(mem, (word_type)-1, exit_status);
    set_stack_pointer(cpu, -1);  // reset the stack
    set_base_pointer(cpu, -1);
    set_word(mem, instr_pointer(cpu), HALT); // update next instruction so machine halts ...
}

INLINE struct kernel_type *new_kernel(FUNC_SIGNATURE((*sys_calls[256])), file_node_type *opened_files, virtual_memory_type *mem)
{
    struct kernel_type *kernel = malloc(sizeof(struct kernel_type));

    set_calls(
        kernel,
        sys_calls ? sys_calls :
        ((FUNC_SIGNATURE((*[]))) {
            [0 ... 255] = __invalid_system_call__,
            [SYS_CALL_EXIT] = __exit__,
            [SYS_CALL_OPEN] = __open__,
            [SYS_CALL_READ] = __read__,
            [SYS_CALL_WRITE] = __write__,
            [SYS_CALL_CLOSE] = __close__,
            [SYS_CALL_TELL] = __tell__,
            [SYS_CALL_SEEK] = __seek__
        })
    );

    set_opened_files(
        kernel,
        opened_files ? opened_files :
            new_file_node(mem, SYS_STD_IN, stdin,
                new_file_node(mem, SYS_STD_OUT, stdout,
                    new_file_node(mem, SYS_STD_ERROR, stderr,
                        NULL)))
    );

    return kernel;
}