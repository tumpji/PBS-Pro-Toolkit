set -e 
set -u


ROOTDIR=/storage/praha1/home/${USER}/
GITDIR=/storage/praha1/home/${USER}/PBS-Pro-Toolkit
AUTHENTICATION=/storage/praha1/home/${USER}/AUTHENTICATION.ini


echo "Building Experiment '$1'"

while true; do
    read -p "Do you wish to build this environment? " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

ACT_STEP=1
STEPS=2

# 1
echo "($ACT_STEP/$STEPS) Create output directories ..."
mkdir "$ROOTDIR/output"    2>/dev/null || true
mkdir "$ROOTDIR/output/$1" 2>/dev/null || true
mkdir "$ROOTDIR/containers" 2>/dev/null || true
mkdir "$ROOTDIR/qsubscripts" 2>/dev/null || true

OUTPUT_DIR="$ROOTDIR/output/$1"


# 2
ACT_STEP=$((ACT_STEP + 1))
echo "($ACT_STEP/$STEPS) Building container ..."

SINGULARITY_DEFINITION_DIR="${GITDIR}/create_singularity/projects/"
SINGULARITY_DEFINITION_PATH_TEMPLATE="${SINGULARITY_DEFINITION_DIR}/template.deffile"
SINGULARITY_DEFINITION_PATH="${SINGULARITY_DEFINITION_DIR}/$1.def"
SINGULARITY_SIF_PATH="${ROOTDIR}/containers/$1.sif"

while true; do
    read -p "Do you wish to use default singularity definition file? " yn
    case $yn in
        [Yy]* ) 
		if [ -e "${SINGULARITY_SIF_PATH}" ]; then
			echo "\tContainer found"
		else
			cp "${SINGULARITY_DEFINITION_PATH_TEMPLATE}" "${SINGULARITY_DEFINITION_PATH}"
			make -C ${SINGULARITY_DEFINITION_DIR} "$1.sif"
			mv "${SINGULARITY_DEFINITION_DIR}/$1.sif" "${SINGULARITY_SIF_PATH}"
		fi
		break;;
        [Nn]* ) echo "Finding containers ..."
		if [ -e "${SINGULARITY_SIF_PATH}" ]; then
			echo "\tContainer found"
		elif [ -e "${SINGULARITY_DEFINITION_PATH}" ]; then
			echo "\tContainer not found but there is definition file available..."
			echo "\tBuilding ..."
			make -C ${SINGULARITY_DEFINITION_DIR} "$1.sif"
			mv "${SINGULARITY_DEFINITION_DIR}/$1.sif" "${SINGULARITY_SIF_PATH}"
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



# 3
ACT_STEP=$((ACT_STEP + 1))
echo "($ACT_STEP/$STEPS) Creating qsub script ..."

QSUB_TEMPLATE_PATH="${GITDIR}/create_singularity/qsub_template.sh"
QSUB_OUTPUT_PATH="${GITDIR}/create_singularity/qsub_template.sh"

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

	# check if something is missing...
	if grep -q AUTO_FILL_IN "${QSUB_OUTPUT_PATH}"; then
		echo "Auto fill in error: something is missing..."
		exit 1
	fi
fi


# 4
ACT_STEP=$((ACT_STEP + 1))
echo "($ACT_STEP/$STEPS) Running qsub script ..."
echo "TODO"

