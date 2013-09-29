
CC = gcc
# CC = clang -Wno-initializer-overrides
CFLAGS = -Wall -O3

all: build

build:
		$(CC) $(CFLAGS) -c -fPIC cpu.c virtual_memory.c kernel.c
		$(CC) -shared -o libvm.so cpu.o virtual_memory.o kernel.o
clean:
		rm *.o
		rm libvm.so

test: test_cpu test_virtual_memory

test_cpu:
		$(CC) $(CFLAGS) test_cpu.c -L. -lvm -o test_cpu
		./test_cpu
		rm test_cpu

test_virtual_memory:
		$(CC) $(CFLAGS) test_virtual_memory.c -L. -lvm -o test_vm
		./test_vm
		rm test_vm


