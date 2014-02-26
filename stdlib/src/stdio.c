

#include <stdio.h>
#include <stdarg.h>

#define system_call_int_type long long

extern system_call_int_type __open__(const char *, const char *);  // returns file_id on success or -1 of failure.
extern system_call_int_type __read__(system_call_int_type, char *, unsigned system_call_int_type);  // returns the number of elements read on success or -1 on failure
extern system_call_int_type __write__(system_call_int_type, char *, unsigned system_call_int_type);  // returns 0 on success or -1 on failure.
extern system_call_int_type __close__(system_call_int_type);  // returns 0 on success or -1 on failure
extern system_call_int_type __tell__(system_call_int_type);
extern system_call_int_type __seek__(system_call_int_type, system_call_int_type, system_call_int_type);


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
    system_call_int_type file_id = __open__(file_path, mode);
    if (file_id < 0)
        return NULL;

    FILE *file = malloc(sizeof(FILE));  // rand() is opening file which is allocating buffer ...

    set_file_number(file, file_id);
    set_file_buffer_index(file, 0);
    set_file_state(file, ((*mode == 'a' || *mode == 'w') ? FILE_READY_FOR_WRITING : FILE_READY_FOR_READING));

    return file;
}

size_t fread(void *dest, size_t size_of_element, size_t number_of_elements, FILE *file)
{   return __read__(file_number(file), dest, size_of_element * number_of_elements)/size_of_element; }


size_t fwrite(const void *src, size_t size, size_t count, FILE *file)
{
    unsigned char *source = src;
    size_t total = (size * count) / sizeof(unsigned char);
    while (total--)
        if (fputc(*source++, file) == EOF)
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
        fread(file_buffer(file), 1, FILE_BUFFER_SIZE, file);
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
    if (file_state(file) != FILE_READY_FOR_WRITING
        || __write__(file_number(file), file_buffer(file), file_buffer_index(file)))
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

static FILE stdout = {1, FILE_READY_FOR_WRITING};

char number_to_char_table[256] = {
    [0 ... 255] = '?',
    [0] = '0', [1] = '1', [2] = '2', [3] = '3', [4] = '4', [5] = '5', [6] = '6', [7] = '7', [8] = '8', [9] = '9',
    [10] = 'a', [11] = 'b', [12] = 'c', [13] = 'd', [14] = 'e', [15] = 'f'
};

char *number_to_string(long long signed_value, int base, char *dest, unsigned long long max_size)
{                                       // base == -10 signals the value to be interpreted as an unsigned decimal
    if ((base < 2 || base > 16) && (base != -10))  // if base is out range, then quit ...
        return NULL;

    char *destination = dest;
    unsigned long long value = signed_value; // interpret signed value as unsigned ...
    if (base == 10 && signed_value < 0) // if working with base 10 and value is negative
    {
        value *= -1;
        *destination++ = '-';
    }
    if (base < 0)
        base *= -1;

    value &= max_size;  // in case we are working with something smaller than long long (like int)
    while (value >= base)
    {
        *destination++ = digit_ch(value % base);  // get least significant digit ...
        value /= base;        // remove it ...
    }
    *destination++ = digit_ch(value % base);      // 0 <= current < base
    *destination-- = '\0';   // terminate string, values are in reverse order ...

    char ch, *temp = dest + (*dest == '-');  // skip initial '-' if it was set ...
    while (destination > temp) // swap characters ...
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
    char *current = dest = lltoa((long long int)value, dest, 10);
    while (*++current); //loc end; safe to assume that lltoa at the very least returns '0' so we can pre-increment.
    *current++ = '.';

    // TODO: find a better method for locating fraction, this isn't accurate
                      // We need to negate the difference if value less than 0.
    double fraction = (value < 0 ? -1.0 : 1.0) * (value - (long long int)value);
    unsigned long long numeric_fraction = fraction * 100000000000000000LL;

    while (fraction && (fraction *= 10.0) < 1.0)    // set leading zeros
        *current++ = '0';
    current = lltoa(numeric_fraction, current, 10);

    // search for '\0'
    while (*++current); // again assume that lltoa at the very least returns '0'
    while (*--current == '0'); // remove/skip any trailing zeros.

    if (*current == '.') // if they where all trailing 0s than just add one more
        *++current = '0';

    *++current = '\0'; // terminate string.

    return dest;
}


int printf(const char *format, ...)
{
    va_list args;
    va_start(args, format);

    char temp[128];
    char *str;
    unsigned long long int total = 0;
    long long value, is_negative;

    #define _error_unknown_specifier(format) printf("Unknown Specifier found!"), exit(-1);
    #define _puts(values) fputs(values, &stdout)


    #define NUMERIC_CASES(default_type, func)                       \
        case 'i': case 'd': total += _puts(func(va_arg(args, default_type), temp, 10)); break ;                           \
        case 'u': total += _puts(func((unsigned long long)va_arg(args, unsigned default_type), temp, -10)); break ;        \
        case 'X': total += _puts(upper(func((unsigned long long)va_arg(args, unsigned default_type), temp, 16))); break ; \
        case 'x': total += _puts(func((unsigned long long)va_arg(args, unsigned default_type), temp, 16)); break ;        \
        case 'o': total += _puts(func((unsigned long long)va_arg(args, unsigned default_type), temp, 8)); break ;         \
        default: _error_unknown_specifier(*(format - 1)); return total;

    while (*format)
        if (*format == '%' && format++) // %*
            switch (*format++)
            {
                // lengths
                case 'h':
                    if (*format == 'h' && format++) switch (*format++) { NUMERIC_CASES(char, itoa) } // %hh*
                    else switch (*format++) { NUMERIC_CASES(short int, itoa) } // %h*
                    break ;

                case 'l':
                    if (*format == 'l' && format++) switch (*format++) { NUMERIC_CASES(long long int, lltoa) } // %ll*
                    else switch (*format++) { NUMERIC_CASES(long int, ltoa) } // %l*
                    break ;

                // default specifiers no length ...
                case '%': putchar('%'); total++;                                                        break ;
                case 'c': putchar(va_arg(args, char)); total++;                                         break ;
                case 's': total += _puts(va_arg(args, char *));                                         break ;
                case 'p': total += _puts("0x"); total += _puts(lltoa(va_arg(args, void *), temp, 16));  break ;
                case 'F': case 'f': total += _puts(float_to_string(va_arg(args, double), temp));        break ;

                NUMERIC_CASES(int, itoa)
            }
        else
            putchar(*format++), total++;

    #undef _puts
    #undef NUMERIC_CASES
    #undef _error_unknown_specifier

    fflush(&stdout);
    return total;
}