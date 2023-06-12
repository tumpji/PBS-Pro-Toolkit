OBJECTS=$(patsubst %.def,%.sif,$(wildcard *.def))


all-tests: ${OBJECTS}


%.sif: %.def
	-@echo Building project $(basename $@) ...
	singularity build --fakeroot $@ $<


