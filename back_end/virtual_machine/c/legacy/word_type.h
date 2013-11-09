
#ifndef _WORD_TYPE_H_
#define _WORD_TYPE_H_

#ifdef __GCC__
    // gcc will take it as a suggestion other compilers will actually inline it, which may cause linking issues ...
    #define INLINE inline
#else
    #define INLINE
#endif

#define BYTE_BIT_SIZE 8

#define _type_ long long int
#define float_type double
#define WORD_PRINTF_FORMAT "%llu"

#define word_type unsigned _type_
#define signed_word_type signed _type_

#define WORD_SIZE sizeof(word_type)

#endif
