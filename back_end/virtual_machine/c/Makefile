
# CC = /Users/samyvilar/Developer/gcc_4.7.2/bin/gcc
CC = gcc
flags = -Wall -Ofast -mtune=native -march=native

virtual_memory = vm
cpu = cpu

all: build

build:
		$(CC) $(flags) -c -fPIC $(virtual_memory).c $(cpu).c
		$(CC) -shared -o libvm.so $(cpu).o $(virtual_memory).o
        
clean:
		rm *.o
		rm libvm.so

test: build test_cpu

test-cpu:
		$(CC) $(flags) test_cpu.c -L. -lvm -o test_cpu
		time ./test_cpu
		rm test_cpu


build-clang:
		clang $(flags) -c -Wno-initializer-overrides -fPIC $(virtual_memory).c $(cpu).c
		clang -shared -o libvm.so $(cpu).o $(virtual_memory).o

test-clang-cpu: build-clang
		clang $(flags) test_cpu.c -L. -lvm -o test_cpu
		time ./test_cpu
		rm test_cpu


UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    shared_object_flag = -shared
endif
ifeq ($(UNAME_S),Darwin)
    shared_object_flag = -dynamiclib
endif


build-icc:
		icc -Wall -Ofast -m64 -xhost -fp-model fast -fomit-frame-pointer -c -fPIC $(virtual_memory).c $(cpu).c
		icc $(shared_object_flag) -o libvm.so $(cpu).o $(virtual_memory).o

test-icc-cpu:
		icc -m64 -Ofast -xhost test_cpu.c -L. -lvm -o test_cpu
		icc $(shared_object_flag) -o libvm.so $(cpu).o $(virtual_memory).o
		time ./test_cpu
		rm test_cpu


test-icc: build-icc test-icc-cpu
