

#ifndef _UNISTD_H_
#define _UNISTD_H_

extern void *__base_heap_ptr__;
extern void *__heap_ptr__;

int brk(void *);
void *sbrk(size_t);


#endif
