
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
#define _WORD_PRINTF_FORMAT WORD_PRINTF_FORMAT
#define SIGNED_WORD_PRINTF_FORMAT "%lli"

#define HALF_WORD_PRINTF_FORMAT "%u"
#define _HALF_WORD_PRINTF_FORMAT HALF_WORD_PRINTF_FORMAT
#define SIGNED_HALF_WORD_PRINTF_FORMAT "%d"

#define QUARTER_WORD_PRINTF_FORMAT "%hu"
#define _QUARTER_WORD_PRINTF_FORMAT QUARTER_WORD_PRINTF_FORMAT
#define SIGNED_QUARTER_WORD_PRINTF_FORMAT "%hi"

#define ONE_EIGHTH_WORD_PRINTF_FORMAT "%hhu"
#define _ONE_EIGHTH_WORD_PRINTF_FORMAT ONE_EIGHTH_WORD_PRINTF_FORMAT
#define SIGNGED_ONE_EIGHTH_WORD_PRINTF_FORMAT "%hhi"

#define get_printf_format(_t_) _t_ ## _WORD_PRINTF_FORMAT
#define get_printf_signed_format(_t_) SIGNED ## _t_ ## _WORD_PRINTF_FORMAT

#define word_type unsigned _word_
#define signed_word_type signed _word_

#define half_word_type unsigned _half_word_
#define signed_half_word_type signed _half_word_

#define quarter_word_type unsigned _quarter_word_
#define signed_quarter_word_type signed _quarter_word_

#define one_eighth_word_type unsigned _one_eighth_word_
#define signed_one_eighth_word_type signed _one_eighth_word_

#define _c_type             word_type
#define _HALF_c_type        half_word_type
#define _QUARTER_c_type     quarter_word_type
#define _ONE_EIGHTH_c_type  one_eighth_word_type
#define get_c_type(_t_) _t_ ## _c_type
#define get_unsigned_c_type get_c_type

#define SIGNED_WORD_TYPE                signed_word_type
#define SIGNED_HALF_WORD_TYPE           signed_half_word_type
#define SIGNED_QUARTER_WORD_TYPE        signed_quarter_word_type
#define SIGNED_ONE_EIGHTH_WORD_TYPE     signed_one_eighth_word_type
#define get_signed_c_type(_t_)          SIGNED ## _t_ ## _WORD_TYPE

#define get_c_size(_t_)         (sizeof(get_c_type(_t_)))
#define WORD_SIZE               get_c_size()

#define HALF_WORD_SIZE          get_c_size(_HALF)
#define _HALF_WORD_SIZE         HALF_WORD_SIZE

#define _QUARTER_WORD_SIZE      get_c_size(_QUARTER)
#define QUARTER_WORD_SIZE       _QUARTER_WORD_SIZE

#define _ONE_EIGHTH_WORD_SIZE   get_c_size(_ONE_EIGHTH)
#define ONE_EIGHTH_WORD_SIZE   _ONE_EIGHTH_WORD_SIZE



#define IMPL_FLOAT_TYPES ,_HALF
#define IMPL_WORD_TYPES IMPL_FLOAT_TYPES, _QUARTER, _ONE_EIGHTH
#endif
