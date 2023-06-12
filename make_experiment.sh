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

# source - git
SINGULARITY_TEMPLATE_DIR="${GITDIR}/create_singularity/templates"
# custom source or cache
SINGULARITY_DEF_PATH="${SINGULARITY_DEFINITION_DIR}/${EXPNAME}.def"
SINGULARITY_SIF_PATH="${CONTAINER_DIR}/${EXPNAME}.sif"

function build_singularity_container {
    # 1: .sif destination
    # 2: .def source
    singularity build --fakeroot "$1" "$2"
}


if [ ! -e "${SINGULARITY_SIF_PATH}" && ! -e "${SINGULARITY_DEF_PATH}" ];
then
	echo "You need to provide definition path for your singularity container"

	while true;
    do
	    read -p "Do you wish to use default singularity definition file? " yn
	    case $yn in
        1)
            echo "You have selected modcma template"
            make -C "${SINGULARITY_TEMPLATE_DIR}" "modcma.sif"
            ln -s "${SINGULARITY_TEMPLATE_DIR}/modcma.sif" "${SINGULARITY_SIF_PATH}"
            ;;
		[Nn]* )
            echo "Aborting..."
            exit 1
            ;;
		* )
            echo "Please answer yes or no."
            ;;
	    esac
    done
elif [ ! -e "${SINGULARITY_SIF_PATH}" && -e "${SINGULARITY_DEF_PATH}" ];
then
    echo "Building container based on ${SINGULARITY_DEF_PATH}"
    build_singularity_container "${SINGULARITY_SIF_PATH}" "${SINGULARITY_DEF_PATH}"
elif [ -e "${SINGULARITY_SIF_PATH}" && -e "${SINGULARITY_DEF_PATH}" &&
	"${SINGULARITY_SIF_PATH}" -ot "${SINGULARITY_DEF_PATH} ];
then
    echo "Found newer definition, do you wish to rebuild the container?
    while true; do
	    read -p "Do you wish rebuild singularity definition file? " yn
	    case $yn in
            [Yy]* )
                build_singularity_container "${SINGULARITY_SIF_PATH}" "${SINGULARITY_DEF_PATH}"
                ;;
            [Nn]* )
                break
                ;;
            * ) echo "Please answer yes or no.";;
	    esac
	done
else
    echo "Found .sif in ${SINGULARITY_SIF_PATH}"
fi
	

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
