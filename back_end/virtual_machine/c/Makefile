
CC = gcc
flags = -Wall -O3 -Wno-initializer-overrides -mtune=native -march=native

virtual_memory = fast_vm
cpu = really_fast_cpu

all: build

#$(CC) $(flags) -c bit_hash.c $(virtual_memory).c $(cpu).c kernel.c
#ar rcs libvm.a bit_hash.o $(cpu).o $(virtual_memory).o kernel.o
build:
		$(CC) $(flags) -c -fPIC bit_hash.c $(virtual_memory).c $(cpu).c kernel.c
		$(CC) -dynamiclib -o libvm.so bit_hash.o $(cpu).o $(virtual_memory).o kernel.o
#		$(CC) -shared -o libvm.so bit_hash.o $(cpu).o $(virtual_memory).o kernel.o

clean:
		rm *.o
		rm libvm.so

test: test_cpu test_virtual_memory

test_cpu:
		$(CC) $(flags) test_cpu.c -L. -lvm -o test_cpu
		time ./test_cpu
		rm test_cpu

test_virtual_memory:
		$(CC) $(flags) test_$(virtual_memory).c -L. -lvm -o test_vm
		time ./test_vm
		rm test_vm

build-icc:
		icc -Wall -O3 -m64 -xhost -fp-model strict -fomit-frame-pointer -c -fPIC bit_hash.c $(virtual_memory).c $(cpu).c kernel.c
		icc -dynamiclib -o libvm.so bit_hash.o $(cpu).o $(virtual_memory).o kernel.o
        
test-icc:
		icc -m64 -O3 -xhost test_cpu.c -L. -lvm -o test_cpu
		icc -m64 -O3 test_$(virtual_memory).c -L. -lvm -o test_vm
		icc -dynamiclib -o libvm.so bit_hash.o $(cpu).o $(virtual_memory).o kernel.o
		time ./test_cpu
		rm test_cpu
		time ./test_vm
		rm test_vm
