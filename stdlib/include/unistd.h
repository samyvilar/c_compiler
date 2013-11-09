

#ifndef _UNISTD_H_
#define _UNISTD_H_

extern const void *__base_heap_ptr__;
extern void *__heap_ptr__;

int brk(void *);
void *sbrk(int);


#endif