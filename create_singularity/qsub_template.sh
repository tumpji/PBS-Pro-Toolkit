#!/bin/sh
#PBS -N myJobName
#PBS -l select=1:ncpus=1:mem=8gb:scratch_local=10g
#PBS -l walltime=2:00:00
#PBS -j oe
#PBS -m ae
#PBS -o /storage/praha1/home/tumpji/logs

set -e
set -u

# environment
SINGULARITY_CONTAINER_PATH=<AUTO_FILL_IN_SINGULARITY_CONTAINER_PATH>
OUTPUT_DIR=<AUTO_FILL_IN_OUTPUT_DIR>
AUTHENTICATION_FILE=<AUTO_FILL_IN_AUTHENTICATION_PATH>



echo "Start Log: ----------------------------------"
env
echo "\tHostname: `hostname -f`"
echo "\tScratch path: $SCRATCHDIR"

echo "\tSINGULARITY CONTAINER PATH: ${SINGULARITY_CONTAINER_PATH}"
echo "\tOUTPUT_DIR: ${OUTPUT_DIR}"
echo "End Log: ----------------------------------"



# this information helps to find a scratch directory in case the job fails and you need to remove the scratch directory manually 
echo "$PBS_JOBID is running on node `hostname -f` in a scratch directory $SCRATCHDIR" >> $OUTPUT_DIR/jobs_info.txt

# test if scratch directory is set
test -n "$SCRATCHDIR" || { echo >&2 "Variable SCRATCHDIR is not set!"; exit 1; }



################
## make the environment

cd $SCRATCHDIR

# copy the container 
cp "${SINGULARITY_CONTAINER_PATH}" container.sif || { echo >&2 "Error while copying the container file!"; exit 2; }

# copy the auth. file
cp "${AUTHENTICATION_FILE}" AUTHENTICATION.ini

# link output
ln -s "${OUTPUT_DIR}" output


############
# Now: in `pwd`:
# output ---> ${OUTPUT_DIR}
# container.sif
# AUTHENTICATION.ini
# 

singularity run container.sif



# clean the SCRATCH directory
clean_scratch


