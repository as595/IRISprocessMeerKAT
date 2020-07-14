
# The IRIS MeerKAT Pipeline

The IRIS MeerKAT pipeline is a radio interferometric calibration pipeline designed to process MeerKAT data. It is built on the [IDIA MeerKAT pipeline](https://github.com/idia-astro/pipelines) **It is under heavy development, and so far only implements the cross-calibration steps, and quick-look images.**

## Requirements

This pipeline is designed to run on the IRIS grid infrastructure, making use of DIRAC and MPICASA. Currently, use of the pipeline requires access to the IRIS SKA VO.

## Quick Start

### 1. In order to use the `IRISprocessMeerKAT.py` script, source the `setup.sh` file:

        source setup.sh

which will add the correct paths to your `$PATH` and `$PYTHONPATH` in order to correctly use the pipeline. We recommend you add this to your `~/.profile`, for future use.

### 2. Build a config file:

To build a configuration file for IRIS the standard command is used followed by the `-I` flag:

        processMeerKAT.py -B -C myconfig.txt -M mydata.ms -I

This defines several variables that are read by the pipeline while calibrating the data, as well as specifying the IRIS parameters. The config file parameters are described by in-line comments in the config file itself wherever possible.

### 3. To create pipeline scripts for IRIS:

        processMeerKAT.py -R -C myconfig.txt -I

This will create a set of shell scripts and JDL files for submitting to IRIS as DIRAC jobs.

Other Ilifu processMeerKAT housekeeping scripts are not yet available.

For help, run `processMeerKAT.py -h`, which provides a brief description of all the command line arguments.

The documentation for the original Ilifu implementation can be accessed on the [pipelines website](https://idia-pipelines.github.io/docs/processMeerKAT), or on the [Github wiki](https://github.com/idia-astro/pipelines/wiki).
