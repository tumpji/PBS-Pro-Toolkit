#!/bin/bash
set -e 
set -u

# counter of steps
ACT_STEP=1
STEPS=$(grep '^step' $0 | wc -l)

function step {
	echo "($ACT_STEP/$STEPS): $1" 
  ACT_STEP=$((ACT_STEP + 1))
}

if [ $# -lt 1 ]; 
then
	echo "You need to provide the name of the experiment you want to create"
	echo "make_experiment.sh <the-name>"
	echo "make_experiment.sh <the-name> <root-folder>"
	echo "  default <root-folder> is the current directory"
	exit 1
fi

# it is advised to check these settings:
EXPNAME=$1
DIRNAME=${2:-$(pwd)}

ROOTDIR=$DIRNAME
GITDIR=$ROOTDIR/PBS-Pro-Toolkit
AUTHENTICATION=$ROOTDIR/AUTHENTICATION.ini


echo
echo "Building Experiment '${EXPNAME}' in folder '$DIRNAME'"


# -------------------------------------------------
step "Checking files..."

if [ ! $(hostname) != "builder.grid.cesnet.cz" ]; then
	echo "WARNING: You may find it hard to build container on this machine."
	echo "\tconsider switching to builder.grid.cesnet.cz"
fi

if [ ! -d "${ROOTDIR}" ]; then
	echo "Cannot find ROOTDIR -- ${ROOTDIR}"
	exit 1
fi

if [ ! -d "${GITDIR}" ]; then
	echo "Cannot find GITDIR -- ${GITDIR}"
	exit 1
fi

if [ ! -f "${AUTHENTICATION}" ]; then
	echo "Cannot find AUTHENTICATION -- ${AUTHENTICATION}"
	echo "You can copy the template in ${GITDIR}/cloudDB/AUTHENTICATION.ini"
	exit 1
fi

if [ "$(stat -L -c "%A" ${AUTHENTICATION})" != "-r--------" ]; then
	echo "Secure abort."
	echo "Set the ${AUTHENTICATION} file to be user-read only"
	echo "Hint: chmod 0400 ${AUTHENTICATION}"
	exit 1
fi	

while true; do
    read -p "Do you wish to build this environment? " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) echo "Aborting..."; 
		exit 0;;
        * ) echo "Please answer yes or no.";;
    esac
done


# -------------------------------------------------
step "Creating directories..."

mkdir -p "$ROOTDIR/output/${EXPNAME}" 2>/dev/null || true
mkdir -p "$ROOTDIR/logs/${EXPNAME}" 2>/dev/null || true
mkdir "$ROOTDIR/containers" 2>/dev/null || true
mkdir "$ROOTDIR/qsub_scripts" 2>/dev/null || true
mkdir "$ROOTDIR/task_scripts" 2>/dev/null || true

OUTPUT_DIR="$ROOTDIR/output/${EXPNAME}"
LOG_DIR="$ROOTDIR/logs/${EXPNAME}"
CONTAINER_DIR="$ROOTDIR/containers"
QSUB_DIR="$ROOTDIR/qsub_scripts"
TASK_SCRIPTS="$ROOTDIR/task_scripts"


# ------------------------------------------------
step "Building container..."

SINGULARITY_DEFINITION_DIR="${GITDIR}/create_singularity/projects"
SINGULARITY_DEFINITION_PATH_TEMPLATE="${SINGULARITY_DEFINITION_DIR}/template.deffile"
SINGULARITY_DEFINITION_PATH="${SINGULARITY_DEFINITION_DIR}/${EXPNAME}.def"
SINGULARITY_SIF_PATH="${CONTAINER_DIR}/${EXPNAME}.sif"

while true; do
    read -p "Do you wish to use default singularity definition file? " yn
    case $yn in
        [Yy]* ) 
		if [ -e "${SINGULARITY_SIF_PATH}" ]; then
			echo "\tContainer found"
		else
			cp "${SINGULARITY_DEFINITION_PATH_TEMPLATE}" "${SINGULARITY_DEFINITION_PATH}"
			make -C ${SINGULARITY_DEFINITION_DIR} "${EXPNAME}.sif"
			mv "${SINGULARITY_DEFINITION_DIR}/${EXPNAME}.sif" "${SINGULARITY_SIF_PATH}"
		fi
		break;;
        [Nn]* ) echo "Finding containers ..."
		if [ -e "${SINGULARITY_SIF_PATH}" ]; then
			echo "\tContainer found"
		elif [ -e "${SINGULARITY_DEFINITION_PATH}" ]; then
			echo "\tContainer not found but there is definition file available..."
			echo "\tBuilding ..."
			make -C ${SINGULARITY_DEFINITION_DIR} "${EXPNAME}.sif"
			mv "${SINGULARITY_DEFINITION_DIR}/${EXPNAME}.sif" "${SINGULARITY_SIF_PATH}"
		else
			echo "Error: cannot find .sif or .def file"
			echo "Create singularity definition file in ${SINGULARITY_DEFINITION_PATH} and re-run the script."
			echo "You can use pattern in ${SINGULARITY_DEFINITION_PATH_TEMPLATE}"
			exit 1
		fi
		break;;
        * ) echo "Please answer yes or no.";;
    esac
done


# -----------------------------------------------
step "Creating qsub script..."

QSUB_TEMPLATE_PATH="${GITDIR}/create_singularity/qsub_template.sh"
QSUB_OUTPUT_PATH="${QSUB_DIR}/${EXPNAME}.sh"

if [ -e "${QSUB_OUTPUT_PATH}" ]; 
then
	echo "\tqsub script already created"
	echo "\tskipping..."
else
	cp "${QSUB_TEMPLATE_PATH}" "${QSUB_OUTPUT_PATH}"
	# change AUTO_FILL_IN...
	sed "s|<AUTO_FILL_IN_SINGULARITY_CONTAINER_PATH>|${SINGULARITY_SIF_PATH}|" \
		-i "${QSUB_OUTPUT_PATH}"
	sed "s|<AUTO_FILL_IN_OUTPUT_DIR>|${OUTPUT_DIR}|" \
		-i "${QSUB_OUTPUT_PATH}"
	sed "s|<AUTO_FILL_IN_AUTHENTICATION_PATH>|${AUTHENTICATION}|" \
		-i "${QSUB_OUTPUT_PATH}"
	sed "s|<AUTO_FILL_IN_LOGS_PATH>|${LOG_DIR}" \
		-i "${QSUB_OUTPUT_PATH}"

	# check if something is missing...
	if grep -q AUTO_FILL_IN "${QSUB_OUTPUT_PATH}"; then
		echo "Auto fill in error: something is missing..."
		exit 1
	fi
fi


# ------------------------------------------------
step "Making task script..."

cp ${GITDIR}/cloudDB/template_job_creation.py "$TASK_SCRIPTS/${EXPNAME}.py"
ln -s $TASK_SCRIPTS/${EXPNAME}.py ${EXPNAME}.py



