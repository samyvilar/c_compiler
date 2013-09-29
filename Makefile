
all: build

build:
		gcc -Wall -O3 -c -fPIC cpu.c virtual_memory.c kernel.c
		gcc -shared -o libvm.so cpu.o virtual_memory.o kernel.o
clean:
		rm *.o
		rm libvm.so

test: test_cpu test_virtual_memory

test_cpu:
		gcc -O3 test_cpu.c -L. -lvm -o test_cpu
		./test_cpu
		rm test_cpu

test_virtual_memory:
		gcc -O3 test_virtual_memory.c -L. -lvm -o test_vm
		./test_vm
		rm test_vm


