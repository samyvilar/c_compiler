
#ifndef _WORD_TYPE_H_
#define _WORD_TYPE_H_

#ifdef __GCC__
    // gcc will take it as a suggestion other compilers will actually inline it, which may cause linking issues ...
    #define INLINE inline
#else
    #define INLINE
#endif

#define BYTE_BIT_SIZE 8
#define _type_ int
#define _word_ long long _type_
#define _half_word_ _type_
#define _quarter_word_ short _type_
#define _one_eighth_word_ char

#define float_type double
#define FLOAT_SIZE sizeof(float_type)
#define half_float_type float
#define HALF_FLOAT_SIZE sizeof(half_float_type)

#define WORD_PRINTF_FORMAT "%llu"
#define HALF_WORD_PRINTF_FORMAT "%u"
#define QUARTER_WORD_PRINTF_FORMAT "%hu"
#define ONE_EIGHTH_WORD_PRINTF_FORMAT "%hhu"

#define word_type unsigned _word_
#define signed_word_type signed _word_

#define half_word_type unsigned _half_word_
#define signed_half_word_type signed _half_word_

#define quarter_word_type unsigned _quarter_word_
#define signed_quarter_word_type signed _quarter_word_

#define one_eighth_word_type unsigned _one_eighth_word_
#define signed_one_eighth_word_type signed _one_eighth_word_

#define WORD_SIZE sizeof(word_type)
#define HALF_WORD_SIZE sizeof(half_word_type)
#define QUARTER_WORD_SIZE sizeof(quarter_word_type)
#define ONE_EIGHTH_WORD_SIZE sizeof(one_eighth_word_type)

#define IMPL_FLOAT_TYPES ,_HALF
#define IMPL_WORD_TYPES IMPL_FLOAT_TYPES, _QUARTER, _ONE_EIGHTH

#define _c_type word_type
#define _HALF_c_type half_word_type
#define _QUARTER_c_type quarter_word_type
#define _ONE_EIGHTH_c_type one_eighth_word_type
#define get_c_type(_type_) _type_ ## _c_type

#endif
