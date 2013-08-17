

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
#define current_buffer_ptr(file) (file->current)
#define increment_buffer_ptr(file) (file->current++)
#define reset_buffer_ptr(file) (current_buffer_ptr(file) = file_buffer(file))
#define is_file_buffer_full(file) ((current_buffer_ptr(file) - file_buffer(file)) == FILE_BUFFER_SIZE)


#define FILE_READY_FOR_READING 1
#define FILE_READY_FOR_WRITING 2

#define EOF -1


FILE *fopen(const char *file_path, const char *mode)
{
    int file_id = __open__(file_path, mode);

    if (file_id < 0)
        return NULL;

    FILE *file = malloc(sizeof(FILE));
    set_file_number(file, file_id);
    reset_buffer_ptr(file);

    if (*mode == 'a' || *mode == 'w')
        set_file_state(file, FILE_READY_FOR_WRITING);
    else
        set_file_state(file, FILE_READY_FOR_READING);

    return file;
}

size_t fread(void *dest, size_t size_of_element, size_t number_of_elements, FILE *file)
{   return __read__(file_number(file), dest, size_of_element * number_of_elements);    }


size_t fwrite(const void *src, size_t size, size_t count, FILE *file)
{
    size_t total = size * count;
    --src;
    while (total--)
        if (fputc(*(char *)(++src), file) == EOF)
            return ((size * count) - (total + 1)) / count;
    return count;
}


int	fclose(FILE *file)
{
    if (fflush(file) || __close__(file_number(file)))
        return EOF;

    set_file_number(file, -1);
    free(file);

    return 0;
}

int fgetc(FILE *file)
{
    if (is_file_buffer_full(file))
    {
        fread(file_buffer(file), 1, FILE_BUFFER_SIZE, file);
        reset_buffer_ptr(file);
    }

    char temp = *current_buffer_ptr(file);
    if (temp == EOF)
        return EOF;

    increment_buffer_ptr(file);
    return temp;
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
    if (is_file_buffer_full(file))
        if (fflush(file))
            return EOF;

    *current_buffer_ptr(file) = (unsigned char)ch;
    increment_buffer_ptr(file);

    return ch;
}

int	fflush(FILE *file)
{
    if (__write__(file_number(file), file_buffer(file), current_buffer_ptr(file) - file_buffer(file)))
        return EOF;

    reset_buffer_ptr(file);
    return 0;
}


void upper(const char *src, const char *dest)
{
    while (*src)
        if (*src >= 'a' && *src <= 'z')
            *dest++ = 'A' + (*src++ - 'a');
        else
            *dest++ = *src++;
    *dest = *src;
}

char *number_to_string(long long value, int base, char *dest)
{
    if (base < 2 || base > 36)
        return NULL;

    char *destination = dest;
    int negative = (value < 0 && base == 10);
    if (negative)
        *destination++ = '-';

    if (value < 0)
        value *= -1;

    #define digit_ch(__numb__) ((__numb__) + (((__numb__) < 10) ? '0' : 'a'))
    while (value > base)
    {
        *destination++ = digit_ch(value % base);
        value /= base;
    }
    *destination++ = digit_ch(value);
    #undef digit_ch
    *destination-- = '\0';

    char *temp = dest + (negative ? 1 : 0);

    char ch; // swap values ...
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
    dest = number_to_string((long long)value, 10, dest);
    size_t index = 0;
    while (dest[index]) index++;
    dest[index++] = '.';

    // TODO: find a better method for locating fraction, this isn't accurate
    double fraction = value - (long long)value;

    if (!fraction)
        dest[index++] = '0';

    while (fraction - (long long)fraction)
    {
        fraction *= 10;
        dest[index++] = '0' + (long long)fraction % 10;
    }

    return dest;
}

int printf(const char *format, ...)
{
    FILE *stdout = fopen(1, "a");

    va_list args;
    va_start(args, format);

    char temp[128];
    int base = 10;
    unsigned long long total = 0;

    while (*format)
    {
        if (*format == '%')
        {
            ++format;
            if (!*format)
                return -1;
            switch (*format)
            {
                case '%':
                    fputc(*format, stdout);
                    ++total;
                    break ;

                case 'c':
                    fputc(va_arg(args, char), stdout);
                    ++total;
                    break ;

                case 's':
                    total += fputs(va_arg(args, char *), stdout);
                    break ;

                case 'p':
                case 'l':
                case 'x':
                case 'X':
                case 'o':
                case 'u':
                case 'i':
                case 'd':
                    {
                        if (*format == 'p' || *format == 'x' || *format == 'X')
                            base = 16;
                        else if (*format == 'o')
                            base = 8;
                        else
                            base = 10;
                        char *str = number_to_string(va_arg(args, void *), base, temp);
                        if (*format == 'X')
                            upper(str, str);
                        total += fputs(str, stdout);
                        break ;
                    }

                case 'F':
                case 'f':
                    total += fputs(float_to_string(va_arg(args, double), temp), stdout);
                    break ;

                default: // error
                    printf("Unknown Specifier found: %c", *format);
                    return total;
            }
        }
        else
        {
            fputc(*format, stdout);
            ++total;
        }
        ++format;
    }

    fflush(stdout);
    fclose(stdout);
    return total;
}
