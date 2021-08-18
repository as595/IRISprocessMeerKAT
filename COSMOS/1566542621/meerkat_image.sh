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

echo "Field: $3"

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
# full dataset in data directory
mkdir data
/bin/mv *.mms.tar.gz data
cd data
echo ">>> extracting data"
COMMAND="ls *.ms.tar.gz"
for FILE in `eval $COMMAND`
do
tar -xzvf $FILE
done
/bin/ls -la
/bin/rm *.mms.tar.gz
cd ..
echo ">>> data set successfully extracted"
# ========================================================

echo ">>> executing imaging on data"
time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg casa --log2term -c imaging_scripts/image_field.py --config myconfig.txt

#echo ">>> executing cube formation on data"
#time singularity exec --cleanenv --contain --home $PWD:/srv --pwd /srv -C meerkat.xvfb.simg xvfb-run -d casa --log2term -c crosscal_scripts/plotcal_spw.py --config myconfig.txt

# ========================================================
# create outputs:

cp myconfig.txt myconfig_$1.txt
tar -cvzf $3.fits.tar.gz *.fits
#tar -cvzf $3.cube.tar.gz *.contcube

/bin/ls -la
