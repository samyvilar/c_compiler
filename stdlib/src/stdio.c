

#include <stdio.h>
#include <stdarg.h>

extern int __open__(const char *, const char *);  // returns file_id on success or -1 of failure.
extern int __read__(int, char *, unsigned long long);  // returns the number of elements read on success or -1 on failure
extern int  __write__(int, char *, unsigned long long);  // returns 0 on success or -1 on failure.
extern int __close__(int);  // returns 0 on success or -1 on failure
extern int __tell__(int);
extern int __seek__(int, int, int);


#define file_number(file) (file->_id)
#define set_file_number(file, number) (file_number(file) = number)

#define file_state(file) (file->state)
#define set_file_state(file, state) (file_state(file) = state)

#define file_buffer(file) (file->buffer)
#define file_buffer_index(file) (file->buffer_index)
#define set_file_buffer_index(file, value) (file_buffer_index(file) = value)
#define is_file_buffer_full(file) (file_buffer_index(file) == FILE_BUFFER_SIZE)

#define current_char(file) (file_buffer(file)[file_buffer_index(file)])
#define consume_char(file) (file_buffer(file)[(file_buffer_index(file))++])
#define set_char(file, ch) (file_buffer(file)[(file_buffer_index(file))++] = ch)


#define FILE_READY_FOR_READING 1
#define FILE_READY_FOR_WRITING 2


FILE *fopen(const char *file_path, const char *mode)
{
    int file_id = __open__(file_path, mode);
    if (file_id < 0)
        return NULL;

    FILE *file = malloc(sizeof(FILE));
    set_file_number(file, file_id);
    set_file_buffer_index(file, 0);
    set_file_state(file, ((*mode == 'a' || *mode == 'w') ? FILE_READY_FOR_WRITING : FILE_READY_FOR_READING));

    return file;
}

size_t fread(void *dest, size_t size_of_element, size_t number_of_elements, FILE *file)
{   return __read__(file_number(file), dest, size_of_element * number_of_elements);    }


size_t fwrite(const void *src, size_t size, size_t count, FILE *file)
{
    size_t total = size * count;
    while (total--)
        if (fputc(*(char *)(src++), file) == EOF)
            return ((size * count) - (total + 1)) / count;
    return count;
}


int	fclose(FILE *file)
{
    if (fflush(file) || __close__(file_number(file)))
        return EOF;

    set_file_number(file, EOF);
    free(file);

    return 0;
}

int fgetc(FILE *file)
{
    if (file_state(file) != FILE_READY_FOR_READING)
        return EOF;

    if (is_file_buffer_full(file))
    {
        fread(file_buffer(file), sizeof(char), FILE_BUFFER_SIZE, file);
        set_file_buffer_index(file, 0);
    }

    return (current_char(file) == EOF) ? EOF : consume_char(file);
}


int	fputs(const char *src, FILE *file)
{
    while (*src)
        if (fputc(*src, file) != *src++)
            return EOF;
    return 0;
}

int fputc(int ch, FILE *file)
{
    if (is_file_buffer_full(file) && fflush(file))
        return EOF;

    set_char(file, ch);
    return ch;
}

int	fflush(FILE *file)
{
    if (file_state(file) != FILE_READY_FOR_WRITING || __write__(
            file_number(file), file_buffer(file), file_buffer_index(file)
        )
    )
        return EOF;

    set_file_buffer_index(file, 0);
    return 0;
}


char *upper(char *src)
{
    char *temp = (src - 1);
    while (*++temp)
        if (*temp >= 'a' && *temp <= 'z')
            *temp = 'A' + (*temp - 'a');
    return src;
}

char *number_to_string(long long value, int base, char *dest, unsigned long long max_size)
{
    if (base < 2 || base > 36)
        return NULL;

    unsigned long long current = value;
    char *destination = dest;
    if (value < 0)
    {
        if (base == 10)
        {
            *destination++ = '-';
            current = -1 * value;
        }
        else
            current = max_size + value + 1;
    }

    #define digit_ch(__numb__) ((__numb__) + (((__numb__) < 10) ? '0' : ('a' - 10)))
    while (current >= base)
    {
        *destination++ = digit_ch(current % base);
        current /= base;
    }
    *destination++ = digit_ch(current % base);
    #undef digit_ch

    *destination-- = '\0';

    char ch, *temp = (*dest == '-') ? (dest + 1) : dest;  // swap values ..
    while (destination > temp)
    {
        ch = *destination;
        *destination-- = *temp;
        *temp++ = ch;
    }

    return dest;
}

char *float_to_string(double value, char *dest)
{
    // TODO: take into account mantissa, double values can be up to 1024 bits large
    char *current = dest = lltoa((long long)value, dest, 10);
    while (*++current); //loc end; safe to assume that lltoa at the very least returns '0' so we can pre-increment.
    *current++ = '.';

    // TODO: find a better method for locating fraction, this isn't accurate
    // slower but more accurate than incrementing by 10 and sub;
    // we can only or rather should display up to 16 decimal place accuracy according to IEEE 754 double format
                      // We need to negate the difference if value less than 0.
    double fraction = (value < 0 ? -1.0 : 1.0) * (value - (long long)value);
    unsigned long long numeric_fraction = fraction * 100000000000000000LL;
    while (fraction && (fraction *= 10.0) < 1.0)    // set leading zeros
        *current++ = '0';
    current = lltoa(numeric_fraction, current, 10);
    // search for '\0'
    while (*++current); // again assume that lltoa at the very least returns '0'
    while (*--current == '0'); // remove/skip any trailing zeros.

    if (*current == '.') // if they where all trailing 0s than just add one more
        *++current = '0';
    *++current = '\0';

    return dest;
}

static FILE stdout = {1, FILE_READY_FOR_WRITING};

int printf(const char *format, ...)
{
    va_list args;
    va_start(args, format);

    char temp[128];
    char *str;
    int base = 10;
    unsigned long long total = 0;

    #define NUMERIC_CASES(default_type, func, unsigned_max) \
        case 'i': case 'd': total += _puts(func(va_arg(args, default_type), temp, 10)); break ; \
        case 'X': total += _puts(upper(func(va_arg(args, unsigned default_type), temp, 16))); break ; \
        case 'x': total += _puts(func(va_arg(args, unsigned default_type), temp, 16)); break ; \
        case 'o': total += _puts(func(va_arg(args, unsigned default_type), temp, 8)); break ; \
        case 'u': total += _puts(func(va_arg(args, unsigned default_type) % (unsigned_max + 1), temp, 10)); break ; \
        default: _error_unknown_specifier(*format); return total;

    #define _error_unknown_specifier(format) printf("Unknown Specifier found: %c", format);
    #define _puts(values) fputs(values, &stdout)
    while (*format)
    {
        if (*format == '%')
        {
            ++format;
            if (!*format)
                return -1;

            switch (*format)
            {
                // lengths
                case 'h':
                    if (*++format == 'h') switch (*++format) { NUMERIC_CASES(char, itoa, UINT_MAX) }
                    else switch (*format) { NUMERIC_CASES(short int, itoa, UINT_MAX) }
                    break ;

                case 'l':
                    if (*++format == 'l') switch (*++format) { NUMERIC_CASES(long, ltoa, ULLONG_MAX) }
                    else switch (*format) { NUMERIC_CASES(long int, ltoa, ULLONG_MAX) }
                    break ;

                // default specifiers no length ...
                case '%': putchar(*format); ++total; break ;
                case 'c': putchar(va_arg(args, int)); ++total; break ;
                case 's': total += _puts(va_arg(args, char *)); break ;
                case 'p': total += _puts("0x"); total += _puts(lltoa(va_arg(args, void *), temp, 16)); break ;
                case 'F': case 'f': total += _puts(float_to_string(va_arg(args, double), temp)); break ;

                NUMERIC_CASES(int, itoa, UINT_MAX)
            }
            #undef _puts
            #undef NUMERIC_CASES
            #undef _error_unknown_specifier

        }
        else
            putchar(*format), ++total;
        ++format;
    }

    fflush(&stdout);
    return total;
}