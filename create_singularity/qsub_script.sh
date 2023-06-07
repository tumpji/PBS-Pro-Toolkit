#!/bin/sh
#PBS -N myJobName
#PBS -l select=1:ncpus=1:mem=8gb:scratch_local=10g
#PBS -l walltime=2:00:00
#PBS -M tumpji@gmail.com
#PBS -j oe
#PBS -m ae
#PBS -o /storage/praha1/home/tumpji/logs

set -e
set -u

# environment
SINGULARITY_CONT=/storage/praha1/home/tumpji/PBS-Pro-Toolkit/create_singularity/container.sif 
OUTPUTDIR=/storage/praha1/home/tumpji/output/${PBS_JOBNAME}/

mkdir "${OUTPUTDIR}"
cd $SCRATCHDIR


echo "Log:"
echo "\tJob name: $PBS_JOBNAME"
echo "\tJob id: $PBS_JOBID"
echo "\tHostname: `hostname -f`"
echo "\tScratch path: $SCRATCHDIR"

echo "\tSINGULARITY CONT: ${SINGULARITY_CONT}"
echo "\tOUTPUTDIR: ${OUTPUTDIR}"


# this information helps to find a scratch directory in case the job fails and you need to remove the scratch directory manually 
echo "$PBS_JOBID is running on node `hostname -f` in a scratch directory $SCRATCHDIR" >> $OUTPUTDIR/jobs_info.txt

# test if scratch directory is set
test -n "$SCRATCHDIR" || { echo >&2 "Variable SCRATCHDIR is not set!"; exit 1; }

# copy the container 
cp $SINGULARITY_CONT . || { echo >&2 "Error while copying the container file!"; exit 2; }

ln -s $OUTPUTDIR output


############
# Now: in `pwd`:
# output ---> $OUTPUTDIR
# container.sif
# 

singularity run



# clean the SCRATCH directory
clean_scratch



