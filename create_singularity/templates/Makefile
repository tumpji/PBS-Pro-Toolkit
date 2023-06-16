OBJECTS=$(patsubst %.def,%.sif,$(wildcard *.def))

.PHONY: clean

all-tests: ${OBJECTS}


modcma.sif: modcma.def modcma_main.sif
	-@echo "Building project $(basename $@) ..."
	singularity build --fakeroot $@ $<

%.sif: %.def
	-@echo "Building project $(basename $@) ..."
	singularity build --fakeroot $@ $<

clean:
	rm *.sif
