
CC = gcc
# CC = clang -Wno-initializer-overrides
CFLAGS = -Wall -O3

virtual_memory = fast_vm
all: build

build:
		$(CC) $(CFLAGS) -c -fPIC bit_hash.c $(virtual_memory).c cpu.c kernel.c
		$(CC) -shared -o libvm.so bit_hash.o cpu.o $(virtual_memory).o kernel.o
clean:
		rm *.o
		rm libvm.so

test: test_cpu test_virtual_memory

test_cpu:
		$(CC) $(CFLAGS) test_cpu.c -L. -lvm -o test_cpu
		./test_cpu
		rm test_cpu

test_virtual_memory:
		$(CC) $(CFLAGS) test_$(virtual_memory).c -L. -lvm -o test_vm
		./test_vm
		rm test_vm


