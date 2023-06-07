OBJECTS=$(patsubst %.def,%.sif,$(wildcard *.def))


all-tests: ${OBJECTS}


%.sif: %.def
	-@echo Building project $(basename $@) ...
	sed "s/AUTO_FILL_USER/${USER}/" $< -i
	sed "s/AUTO_FILL_COLLECTION/$(basename $@)/" $< -i

	#singularity build --fakeroot $@ $<


