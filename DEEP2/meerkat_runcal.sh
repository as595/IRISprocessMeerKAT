#!/bin/bash
echo "==START=="
/bin/hostname
echo "======="
/bin/ls -la
echo "======="
/bin/date
echo "======="

echo "kernel version check:"
uname -r
echo "shell: $0"

echo "Job ID: $1"

echo "SPW: $3"

echo "No. threads: "
echo $OMP_NUM_THREADS

echo "printing singularity version on grid:"
singularity --version

# ========================================================

echo ">>> extracting scripts"
tar -xvzf IRISprocessMeerKAT.tar.gz
/bin/mv IRISprocessMeerKAT/* .
echo ">>> scripts successfully extracted"

# ========================================================
# keep data in working directory for calibration stage

echo ">>> extracting data"
COMMAND="ls *.mms.tar.gz"
for FILE in `eval $COMMAND`
do
tar -xzvf $FILE
done
/bin/ls -la
/bin/rm *.mms.tar.gz
echo ">>> data set successfully extracted"

# ========================================================
# run calibration:

echo ">>> executing get_partition on data"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c aux_scripts/get_partition.py --config myconfig.txt $3

echo ">>> running flag_round_1.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/flag_round_1.py --config myconfig.txt

echo ">>> running setjy.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/setjy.py --config myconfig.txt

echo ">>> running xx_yy_solve.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/xx_yy_solve.py --config myconfig.txt

echo ">>> running xx_yy_apply.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/xx_yy_apply.py --config myconfig.txt

echo "running flag_round_2.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/flag_round_2.py --config myconfig.txt

echo "running xx_yy_solve.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/xx_yy_solve.py --config myconfig.txt

echo "running xx_yy_apply.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/xx_yy_apply.py --config myconfig.txt

echo "running split.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c crosscal_scripts/split.py --config myconfig.txt

echo "running quick_tclean.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa -c crosscal_scripts/quick_tclean.py --config myconfig.txt
#time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C casameer-5.4.1.xvfb.simg mpicasa -n $OMP_NUM_THREADS casa -c crosscal_scripts/quick_tclean.py --config myconfig.txt


echo ">>> running plot_solutions.py"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg xvfb-run -d casa --nogui --log2term -c crosscal_scripts/plot_solutions.py --config myconfig.txt

# ========================================================
# create outputs:

cp myconfig.txt myconfig_$3.txt
tar -czvf plots_$3.tar.gz plots
tar -czvf images_$3.tar.gz images
tar -czvf caltables_$3.tar.gz caltables
tar -czvf outputMMS_$3.tar.gz *mms*

/bin/ls -la
