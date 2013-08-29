

#ifndef _STDARG_H_
#define _STDARG_H_

#include <stdlib.h>

typedef void * va_list;

#define va_start(var, last_argument) (var = ((void *)(&last_argument + sizeof(last_argument))))
#define va_arg(args, obj_type) (*(((obj_type *)args)++))
#define va_end(args) (args = NULL)

#endif