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

if [ $(hostname) != "builder.grid.cesnet.cz" ]; then
	echo "WARNING: You may find it hard to build container on this machine."
	echo -e "\tconsider switching to builder.grid.cesnet.cz"
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
	echo "You can copy the template in ${GITDIR}/clouddb/AUTHENTICATION.ini"
	exit 1
fi

if [ "$(stat -L -c "%A" ${AUTHENTICATION})" != "-r--------" ]; then
	echo "Secure abort."
	echo "Set the ${AUTHENTICATION} file to be user-read only"
	echo "Hint: chmod 0400 ${AUTHENTICATION}"
	exit 1
fi	

while true; do
    echo
    read -p "Do you wish to build the '$EXPNAME' environment? " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) echo "Aborting...";
		exit 0;;
        * ) echo "Please answer yes or no.";;
    esac
done


# -------------------------------------------------
step "Creating directories..."

function make_directory {
    if [ ! -d "$1" ]; then
        if [ -e "$1" ]; then
            echo "Error: file $1 exists and it is not directory"
        else
            mkdir -p "$1"
        fi
    fi
}

TASK_SCRIPTS="$ROOTDIR/task_scripts"

make_directory "${TASK_SCRIPTS}"


QSUB_DIR="$ROOTDIR/qsub_scripts"
OUTPUT_DIR="$ROOTDIR/output/${EXPNAME}"
LOG_DIR="$ROOTDIR/logs/${EXPNAME}"

make_directory "${QSUB_DIR}"
make_directory "${OUTPUT_DIR}"
make_directory "${LOG_DIR}"


CONTAINER_DIR="$ROOTDIR/containers"
CONTAINER_DEF="$ROOTDIR/containers/def"

make_directory "${CONTAINER_DIR}"
make_directory "${CONTAINER_DEF}"


# ------------------------------------------------
step "Building container..."

# source - git
SINGULARITY_TEMPLATE_DIR="${GITDIR}/create_singularity/templates"
# custom source or cache

SINGULARITY_DEF_PATH="${CONTAINER_DEF}/${EXPNAME}.def"
SINGULARITY_SIF_PATH="${CONTAINER_DIR}/${EXPNAME}.sif"

function build_singularity_container {
    # 1: .sif destination
    # 2: .def source
    singularity build --fakeroot "$1" "$2"
}


if [ ! -e "${SINGULARITY_SIF_PATH}" ];
then
    if [ ! -e "${SINGULARITY_DEF_PATH}" ];
    then
        echo "You need to provide definition path for your singularity container"

        while true;
        do
            echo "Do you wish to use default singularity definition file?"
            echo "You can select following options:"
            echo -e "\t  1) modcma template"
            echo -e "\t no) abort selection"
            read -p "What is your decision? " yn

            case $yn in
            1)
                echo "You have selected modcma template"
                make -C "${SINGULARITY_TEMPLATE_DIR}" "modcma.sif"
                ln -s "${SINGULARITY_TEMPLATE_DIR}/modcma.sif" "${SINGULARITY_SIF_PATH}"
                break
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
    else
        echo "Building container based on ${SINGULARITY_DEF_PATH}"
        build_singularity_container "${SINGULARITY_SIF_PATH}" "${SINGULARITY_DEF_PATH}"
    fi
elif [ "${SINGULARITY_SIF_PATH}" -ot "${SINGULARITY_DEF_PATH}" ];
then
    echo "Found newer definition, do you wish to rebuild the container?"
    while true; do
        echo
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
	echo -e "\tqsub script already created"
	echo -e "\tskipping..."
else
	cp "${QSUB_TEMPLATE_PATH}" "${QSUB_OUTPUT_PATH}"
	# change AUTO_FILL_IN...
	sed "s|<AUTO_FILL_IN_SINGULARITY_CONTAINER_PATH>|${SINGULARITY_SIF_PATH}|" \
		-i "${QSUB_OUTPUT_PATH}"
	sed "s|<AUTO_FILL_IN_OUTPUT_DIR>|${OUTPUT_DIR}|" \
		-i "${QSUB_OUTPUT_PATH}"
	sed "s|<AUTO_FILL_IN_AUTHENTICATION_PATH>|${AUTHENTICATION}|" \
		-i "${QSUB_OUTPUT_PATH}"
	sed "s|<AUTO_FILL_IN_LOGS_PATH>|${LOG_DIR}|" \
		-i "${QSUB_OUTPUT_PATH}"
    sed "s|<AUTO_FILL_IN_COLLECTION>|${EXPNAME}|" \
        -i "${QSUB_OUTPUT_PATH}"

    if grep -q AUTO_FILL_IN_PACKAGE "${QSUB_OUTPUT_PATH}"; then
        echo
        while true; do
            echo ""
            echo "You need to select the source of the main\(kwargs\) function. The options are:"
            echo -e "\t  1) modcma.run_exp"
            echo -e "\t  2) custom package"
            echo -e "\t no) abort selection"
            read -p "What is your decision?" yn

            case $yn in
                1)  SELECTION="modcma.run_exp"
                    break;;
                2)  read -p "What package do you wish to run?" SELECTION
                    break;;
                [Nn]* )
                    break;;
                * ) echo "Please answer 1, 2 or no.";;
            esac
        done
        sed "s|<AUTO_FILL_IN_PACKAGE>|${SELECTION}|" -i "${QSUB_OUTPUT_PATH}"
    fi

	# check if something is missing...
	if grep -q AUTO_FILL_IN "${QSUB_OUTPUT_PATH}"; then
		echo "Auto fill in error: something is missing..."
		exit 1
	fi
fi



# ------------------------------------------------
step "Making task script..."


cp "${GITDIR}/clouddb/scripts/template_job_creation.py" "${TASK_SCRIPTS}/${EXPNAME}.py"
sed "s|#insertpath|import sys;sys.path.append('${GITDIR}')|" -i "${TASK_SCRIPTS}/${EXPNAME}.py"


ln -s "${TASK_SCRIPTS}/${EXPNAME}.py" "${EXPNAME}.py"

