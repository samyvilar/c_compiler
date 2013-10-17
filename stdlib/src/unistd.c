

#include <unistd.h>


extern void *__heap_ptr__;

int brk(void *addr)
{
    __heap_ptr__ = addr;
    return -1 * (__heap_ptr__ != addr);
}

void *sbrk(int size)
{
    void *prev_ptr = __heap_ptr__;
    __heap_ptr__ += size;
    return prev_ptr;
}
