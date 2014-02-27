.PHONY: all test clean stdlib vm

all: vm stdlib

stdlib:
		mkdir -p stdlib/libs
		./cc.py -a stdlib/src/unistd.c stdlib/src/stdlib.c stdlib/src/string.c stdlib/src/stdio.c -o stdlib/libs/libc.p

test:
		nosetests

torture:
		./cc.py test/torture/main.c --vm
		./cc.py test/torture/main_1.c --vm
		./cc.py test/torture/main_2.c --vm
		./cc.py test/torture/main_4.c --vm
		./cc.py test/torture/main_5.c --vm

vm:
		$(MAKE) -C back_end/virtual_machine/c all
clean:
		rm -f stdlib/libs/libc.p
		$(MAKE) -C back_end/virtual_machine/c clean

