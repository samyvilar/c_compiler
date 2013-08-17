
#ifndef _STDLIB_H_
#define _STDLIB_H_

#include <unistd.h>

typedef unsigned long size_t;

#ifndef NULL
    #define NULL ((void *)0)
#endif

int rand();

void* malloc (size_t);
void* calloc (size_t, size_t);
void* realloc (void *, size_t);
void free(void *);


#endif