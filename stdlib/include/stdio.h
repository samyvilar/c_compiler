
#ifndef _STDIO_H_
#define _STDIO_H_

#include <stdlib.h>
#include <limits.h>

#define FILE_BUFFER_SIZE 1024

typedef long long fpos_t;

typedef struct FILE {
    int _id;
    int state;
    char buffer[FILE_BUFFER_SIZE];
    unsigned int buffer_index;
} FILE;

#define EOF -1

int	 fclose(FILE *);
FILE	*fopen(const char *, const char *);
size_t	 fread(void *, size_t, size_t, FILE *);
size_t	 fwrite(const void *, size_t, size_t, FILE *);

int	 fseek(FILE *, long, int);

int	 feof(FILE *);
int	 ferror(FILE *);
int	 fflush(FILE *);
int	 fgetc(FILE *);
long long fgetpos(FILE *, fpos_t *);

char *fgets(char *, int, FILE *);

int	 fputc(int, FILE *);
int	 fputs(const char *, FILE *);


int	 fscanf(FILE *, const char *, ...);

int	 fsetpos(FILE *, const fpos_t *);
long ftell(FILE *);


int	 getc(FILE *);
int	 getchar(void);

char *gets(char *);
void perror(const char *);

int	printf(const char *, ...);

// int	putc(int, FILE *);
#define putchar(value) fputc(value, &stdout)
// int	puts(const char *);
#define puts(value) fputs(value, &stdout), putchar('\n')

int	scanf(const char *, ...);

#define lltoa(value, str, base) number_to_string(value, base, str, ULLONG_MAX)
#define ltoa(value, str, base)  number_to_string(value, base, str, ULLONG_MAX)
#define itoa(value, str, base)  number_to_string(value, base, str, UINT_MAX)

#endif