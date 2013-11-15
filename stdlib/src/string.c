
#include <string.h>


void *memcpy(void *dest, const void *src, size_t numb)
{
    unsigned char
        *dest_values = dest,
        *source_value = src;

    numb /= sizeof(unsigned char);
    while (numb--)
        *dest_values++ = *source_value++;

    return dest;
}

void *memmove(void *dest, const void *src, size_t numb)
{
    if (dest < src)
        return memcpy(dest, src, numb);

    unsigned char
        *destination = dest + numb,
        *source = src + numb;

    numb /= sizeof(unsigned char);
    while (numb--)
        *--destination = *--source;

    return dest;
}

int memcmp(const void *src_0, const void *src_1, size_t numb)
{
    unsigned char
        *source_0 = src_0,
        *source_1 = src_1;

    numb /= sizeof(unsigned char);
    while (numb && *source_0 == *source_1)
        numb--, source_0++, source_1++; // safe guard against numb == 0;

    return numb ? *source_0 - *source_1 : 0;
}

void *memchr(const void *dest, int value, size_t numb)
{
    unsigned char *values = dest;
    numb /= sizeof(unsigned char);
    while (numb && *values != (unsigned char)value)
        numb--, values++;

    return numb ? values : NULL;   // if numb is 0 then byte wasn't found.
}

void *memset(void *dest, int value, size_t numb)
{
    numb /= sizeof(unsigned char);
    unsigned char *destination = dest;

    while (numb--)
        *destination++ = (unsigned char)value;

    return dest;
}


char *strcpy(char *dest, const char *src)
{
    unsigned char *destination = dest;

    while ( (*destination++ = *src++) ) ;

    return dest;
}

char *strncpy(char *dest, const char *src, size_t numb)
{
    unsigned char *destination = dest;
    while (numb && (*destination++ = *src++))
        numb--;

    memset(destination, '\0', numb);
    return dest;
}

char *strcat(char *dest, const char *src)
{
    strcpy((dest + strlen(dest)), src);
    return dest;

}

char *strncat(char *dest, const char *src, size_t numb)
{
    unsigned char *destination = dest + strlen(dest);
    while (numb-- && (*destination++ = *src++)) ;

    if (destination != dest) // safeguard against numb == 0
        *destination = '\0';

    return dest;
}

int strcmp(const char *str1, const char *str2)
{
    while (*str1 && *str2 && *str1 == *str2)
        str1++, str2++;
    return *str1 - *str2;
}

int strncmp(const char *str1, const char *str2, size_t numb)
{
    while (numb && *str1 && *str2 && *str1 == *str2)
        numb--, str1++, str2++;
    return numb ? *str1 - *str2 : 0;
}


char *strchr(const char *str, int ch)
{
    while (*str && *str != (char)ch)
        str++;
    return (*str == (char)ch) ? (char *)str : NULL;
}

size_t strcspn(const char *str, const char *set)
{
    const char *temp = str;
    while (!strchr(set, *str))
        str++;
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
    do
        if (*str == (char)ch)
            temp = (char *)str;
    while (*str++) ;

    return temp;
}

size_t strspn(const char *str, const char *set)
{
    if (!*set) // if set is empty just return 0;
        return 0;

    const char *temp = str;
    while (*str && strchr(set, *str)) // strchr includes '\0' but strspn doesn't
        str++;
    return str - temp;
}

char *strstr(const char *str, const char *sub_str)
{
    if (!(*sub_str && *str)) // return NULL if either is empty ...
        return NULL;

    char *temp = str - 1; // remove one char otherwise infinite loop may occur
    size_t len = strlen(sub_str);  // pre-calculate len
    while (
        (temp = strchr(temp + 1, *sub_str)) // search for first occurrence of matching next, characters updating temp
            &&  // if no match was found (temp == NULL) break ..
        strncmp(temp, sub_str, len) // match was found compare to see if the rest of the chars match ...
    );

    return temp;
}

#ifndef NULL
    #define NULL ((void *)0)
#endif

#include <stdio.h>

char *strtok(char *str, const char *delimiters)
{
    static char *current = NULL;
    char *start = NULL;

    if (str)
        current = str;

    if (*current)
    {
        start = current + strspn(current, delimiters); // search for first occurrence of delimiter if any ...
        current = start + strcspn(start, delimiters);  // search for end of token
        if (*current) // if not at end set '\0' and increment
            *current++ = '\0';
    }

    return start;
}

size_t strlen(const char *str)
{
    const char *temp = str;
    while (*str)
        str++;
    return str - temp;
}