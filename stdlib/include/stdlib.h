
#ifndef _STDLIB_H_
#define _STDLIB_H_

#include <unistd.h>

typedef unsigned long size_t;

#ifndef NULL
    #define NULL ((void *)0)
#endif

int rand();
void srand(unsigned int);

void* malloc (size_t);
//void* calloc (size_t, size_t);
#define calloc(numb_elem, size_of_each) memset(malloc(numb_elem * size_of_each), 0, numb_elem * size_of_each)
void* realloc (void *, size_t);
void free(void *);

void exit(long);


#endif