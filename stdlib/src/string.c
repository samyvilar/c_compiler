
#include <string.h>

#define is_aligned(address, size) (!(((unsigned long)address) & (size - 1)))

#ifdef __SSE2__
    #include <emmintrin.h>

    #define vector_type __m128i
    #define vector_type_bytes(value) _mm_set1_epi8(value)
    #define equaled_vectors(vector_0, vector_1) (_mm_movemask_epi8(_mm_cmpeq_epi32(vector_0, vector_1)))
#else
    #define vector_type void *
    static vector_type _vector_type_bytes(unsigned char value)
    {
        vector_type temp;
        unsigned char *address = &temp;
        while (address != ((void *)&temp) + sizeof(temp))
            *address++ = value;
        return temp;
    }
    #define vector_type_bytes _vector_type_bytes
    #define equaled_vectors(vector_0, vector_1) (vector_0 == vector_1)
#endif


void *memcpy(void *dest, const void *src, size_t numb)
{
    size_t index = 0;
    if (is_aligned(dest, sizeof(vector_type)) && is_aligned(src, sizeof(vector_type)))
        while (numb > sizeof(vector_type))
        {
            *(vector_type *)(dest + index) = *(vector_type *)(src + index);
            index += sizeof(vector_type);
            numb -= sizeof(vector_type);
        }

    while (numb--)
    {
        *(unsigned char *)(dest + index) = *(unsigned char *)(dest + index);
        ++index;
    }

    return dest;
}

void *memmove(void *dest, const void *src, size_t numb)
{
    if (dest < src)
        return memcpy(dest, src, numb);

    if (numb > sizeof(vector_type) &&
            is_aligned((dest + numb - sizeof(vector_type)), sizeof(vector_type)) &&
            is_aligned((src + numb - sizeof(vector_type)), sizeof(vector_type)))
        while (numb > sizeof(vector_type))
        {
            numb -= sizeof(vector_type);
            *(vector_type *)(dest + numb) = *(vector_type *)(src + numb);
        }

    while (numb--)
        *(unsigned char *)(dest + numb) = *(unsigned char *)(src + numb);

    return dest;
}

int memcmp(const void *src_0, const void *src_1, size_t numb)
{
    size_t index = 0;
    if (is_aligned(src_0, sizeof(vector_type)) && is_aligned(src_1, sizeof(vector_type)))
        while (numb > sizeof(vector_type) && equaled_vectors(*(vector_type *)(src_0 + index), *(vector_type *)(src_1 + index)))
        {
            numb -= sizeof(vector_type);
            index += sizeof(vector_type);
        }

    while (numb && (*(unsigned char *)(src_0 + index) == *(unsigned char *)(src_1 + index)))
    {
        ++index;
        --numb; // safe guard against numb == 0;
    }
    return numb ? (*(char *)(src_0 + index) - *(char *)(src_1 + index)) : 0;
}

void *memchr(const void *dest, int value, size_t numb)
{
    size_t index = 0;
    while (numb && *(unsigned char *)(dest + index) != (unsigned char)value)
    {
        --numb;
        ++index;
    }
    return numb ? (void *)(dest + index) : NULL;   // if numb is 0 then byte wasn't found.
}


void *memset(void *dest, int value, size_t numb)
{
    vector_type temp = vector_type_bytes((unsigned char)value);
    void *destination = dest;

    while (numb > sizeof(vector_type) && !is_aligned(dest, sizeof(vector_type))) // align pointer.
    {
        *(unsigned char *)(dest++) = (unsigned char)value;
        --numb;
    }

    while (numb > sizeof(vector_type))    // pointer is aligned, use vector operations, if applicable.
    {
        *(vector_type *)dest = temp;
        dest += sizeof(vector_type);
        numb -= sizeof(vector_type);
    }

    while (numb--)       // set any remaining bytes ...
        *(unsigned char *)(dest++) = (unsigned char)value;

    return destination;
}



char *strcpy(char *dest, const char *src)
{
    size_t index = 0;
    while ( (dest[index] = src[index]) ) ++index;
    return dest;
}

char *strncpy(char *dest, const char *src, size_t numb)
{
    size_t index = 0;
    while (numb && (dest[index] = src[index]))
    {
        --numb;
        ++index;
    }

    memset((dest + index), '\0', numb);
    return dest;
}

char *strcat(char *dest, const char *src)
{
    size_t index = 0;
    while (dest[index])
        ++index;

    strcpy((dest + index), src);
    return dest;

}

char *strncat(char *dest, const char *src, size_t numb)
{
    size_t index = 0;
    while (dest[index])
        ++index;
    while (numb-- && (dest[index] = *src++))
        ++index;
    dest[index] = '\0';
    return dest;
}

int strcmp(const char *str1, const char *str2)
{
    while (*str1 && *str2 && *str1 == *str2)
    {
        ++str1; ++str2;
    }
    return *str1 - *str2;
}

int strncmp(const char *str1, const char *str2, size_t numb)
{
    while (numb && *str1 && *str2 && *str1 == *str2)
    {
        --numb; ++str1; ++str2;
    }
    return numb ? *str1 - *str2 : 0;
}


char *strchr(const char *str, int ch)
{
    --str;
    while (*++str && *str != (char)ch);
    return (*str == (char)ch) ? (char *)str : NULL;
}

size_t strcspn(const char *str, const char *set)
{
    const char *temp = str;
    while (!(strchr(set, *str)))
        ++str;
    return str - temp;
}

char *strpbrk(const char *str, const char *set)
{
    size_t offset = strcspn(str, set);
    return *(str + offset) ? (char *)(str + offset) : NULL;
}

char *strrchr(const char *str, int ch)
{
    char *temp = NULL;
    --str;
    while (*++str)
        if (*str == (char)ch)
            temp = (char *)str;
    return temp;
}

size_t strspn(const char *str, const char *set)
{
    const char *temp = str;
    --str;
    while (strchr(set, *++str));
    return str - temp;
}

char *strstr(const char *str, const char *sub_str)
{
    char *temp = strchr(str, *sub_str);
    size_t len = strlen(sub_str);
    while (temp && strncmp(temp, sub_str, len))
        temp = strchr(temp + 1, *sub_str);
    return temp;
}

char *strtok(char *str, const char *delims)
{
    static char *current = NULL;
    char *start = NULL;

    if (str)
        current = str;

    if (*current)
    {
        start = current + strspn(current, delims); // search for first occurrence of delimiter if any ...
        current = start + strcspn(start + 1, delims) + 1; // search for end of token, include 1 delimiter for '\0'
        *current++ = '\0';
    }


    return start;
}

size_t strlen(const char *str)
{
    const char *temp = str;
    --str;
    while (*++str) ;
    return str - temp;
}




#undef vector_type
#undef vector_type_bytes
#undef equaled_vectors