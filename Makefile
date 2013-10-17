
all: stdlib

stdlib:
		./c_comp.py -a stdlib/src/unistd.c stdlib/src/stdlib.c stdlib/src/string.c stdlib/src/stdio.c -o stdlib/libs/libc.p

test:
		nosetests
		./test_cpu
		rm test_cpu

clean:
		rm stdlib/libs/libc.p

