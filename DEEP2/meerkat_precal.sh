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
mkdir data
/bin/mv *.ms.tar.gz data
cd data
echo ">>> extracting data"
COMMAND="ls *.ms.tar.gz"
for FILE in `eval $COMMAND`
do
tar -xzvf $FILE
done
/bin/ls -la
/bin/rm *.ms.tar.gz
cd ..
echo ">>> data set successfully extracted"
# ========================================================


echo ">>> executing listobs on data"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c aux_scripts/listobs.py --config myconfig.txt

echo ">>> executing get_fields on data"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c aux_scripts/get_fields.py --config myconfig.txt

echo ">>> executing partition on data"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C casameer-5.4.1.xvfb.simg mpicasa -n $OMP_NUM_THREADS casa --log2term -c crosscal_scripts/partition.py --config myconfig.txt $OMP_NUM_THREADS

/bin/ls -la

cp myconfig.txt myconfig_$1.txt

for file in *; do
if [[ $file == *.mms ]]; then
tar -cvzf $file.tar.gz $file
fi
done

/bin/ls -la
