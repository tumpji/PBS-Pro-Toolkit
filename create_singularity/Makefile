
.PHONY: run

run: container.sif
	singularity shell $<

container.sif: container_definition.def requirements.txt
	singularity build $@ $<



