#Copyright (C) 2020 Inter-University Institute for Data Intensive Astronomy
#See processMeerKAT.py for license details.

#!/usr/bin/env python2.7

import os, sys
import argparse
import ConfigParser
import ast

import globals
import logger

# ========================================================================================================
# ========================================================================================================

def parse_args():
    
    """Parse arguments into this script.
        
        Returns:
        --------
        args : class ``argparse.ArgumentParser``
        Known and validated arguments."""
    
    def parse_scripts(val):
        
        """Format individual arguments passed into a list for [ -S --scripts] argument, including paths and boolean values.
            
            Arguments/Returns:
            ------------------
            val : bool or str
            Path to script or container, or boolean representing whether that script is threadsafe (for MPI)."""
        
        if val.lower() in ('true','false'):
            return (val.lower() == 'true')
        else:
            return check_path(val)

    parser = argparse.ArgumentParser(prog=globals.THIS_PROG,description='Process MeerKAT data via CASA measurement set. Version: {0}'.format(globals.__version__))

    parser.add_argument("-M","--MS",metavar="path", required=False, type=str, help="Path to measurement set.")
    parser.add_argument("-C","--config",metavar="path", default=globals.CONFIG, required=False, type=str, help="Relative (not absolute) path to config file.")
    parser.add_argument("-N","--nodes",metavar="num", required=False, type=int, default=1,
                        help="Use this number of nodes [default: 1; max: {0}].".format(globals.TOTAL_NODES_LIMIT))
    parser.add_argument("-t","--ntasks-per-node", metavar="num", required=False, type=int, default=8,
                        help="Use this number of tasks (per node) [default: 16; max: {0}].".format(globals.NTASKS_PER_NODE_LIMIT))
    parser.add_argument("-D","--plane", metavar="num", required=False, type=int, default=1,
                        help="Distribute tasks of this block size before moving onto next node [default: 1; max: ntasks-per-node].")
    parser.add_argument("-m","--mem", metavar="num", required=False, type=int, default=globals.MEM_PER_NODE_GB_LIMIT,
                        help="Use this many GB of memory (per node) for threadsafe scripts [default: {0}; max: {0}].".format(globals.MEM_PER_NODE_GB_LIMIT))
    parser.add_argument("-p","--partition", metavar="name", required=False, type=str, default="Main", help="SLURM partition to use [default: 'Main'].")
    parser.add_argument("-T","--time", metavar="time", required=False, type=str, default="12:00:00", help="Time limit to use for all jobs, in the form d-hh:mm:ss [default: '12:00:00'].")
    parser.add_argument("-S","--scripts", action='append', nargs=3, metavar=('script','threadsafe','container'), required=False, type=parse_scripts, default=globals.SCRIPTS,
                        help="Run pipeline with these scripts, in this order, using these containers (3rd value - empty string to default to [-c --container]). Is it threadsafe (2nd value)?")
    parser.add_argument("-b","--precal_scripts", action='append', nargs=3, metavar=('script','threadsafe','container'), required=False, type=parse_scripts, default=globals.PRECAL_SCRIPTS, help="Same as [-S --scripts], but run before calibration.")
    parser.add_argument("-a","--postcal_scripts", action='append', nargs=3, metavar=('script','threadsafe','container'), required=False, type=parse_scripts, default=globals.POSTCAL_SCRIPTS, help="Same as [-S --scripts], but run after calibration.")
    parser.add_argument("-w","--mpi_wrapper", metavar="path", required=False, type=str, default=globals.MPI_WRAPPER,
                        help="Use this mpi wrapper when calling threadsafe scripts [default: '{0}'].".format(globals.MPI_WRAPPER))
    parser.add_argument("-c","--container", metavar="path", required=False, type=str, default=globals.CONTAINER, help="Use this container when calling scripts [default: '{0}'].".format(globals.CONTAINER))
    parser.add_argument("-n","--name", metavar="unique", required=False, type=str, default='', help="Unique name to give this pipeline run (e.g. 'run1_'), appended to the start of all job names. [default: ''].")
    parser.add_argument("-d","--dependencies", metavar="list", required=False, type=str, default='', help="Comma-separated list (without spaces) of SLURM job dependencies (only used when nspw=1). [default: ''].")
    parser.add_argument("-e","--exclude", metavar="nodes", required=False, type=str, default='', help="SLURM worker nodes to exclude [default: ''].")
    parser.add_argument("-A","--account", metavar="group", required=False, type=str, default='b03-idia-ag', help="SLURM accounting group to use (e.g. 'b05-pipelines-ag' - check 'sacctmgr show user $(whoami) -s format=account%%30') [default: 'b03-idia-ag'].")
    parser.add_argument("-r","--reservation", metavar="name", required=False, type=str, default='', help="SLURM reservation to use. [default: ''].")

    parser.add_argument("-l","--local", action="store_true", required=False, default=False, help="Build config file locally (i.e. without calling srun) [default: False].")
    parser.add_argument("-s","--submit", action="store_true", required=False, default=False, help="Submit jobs immediately to SLURM queue [default: False].")
    parser.add_argument("-v","--verbose", action="store_true", required=False, default=False, help="Verbose output? [default: False].")
    parser.add_argument("-q","--quiet", action="store_true", required=False, default=False, help="Activate quiet mode, with suppressed output [default: False].")
    parser.add_argument("-P","--dopol", action="store_true", required=False, default=False, help="Perform polarization calibration in the pipeline [default: False].")
    parser.add_argument("-2","--do2GC", action="store_true", required=False, default=False, help="Perform (2GC) self-calibration in the pipeline [default: False].")
    parser.add_argument("-x","--nofields", action="store_true", required=False, default=False, help="Do not read the input MS to extract field IDs [default: False].")
    parser.add_argument("-I","--iris", action="store_true", required=False, default=False, help="Create pipeline for IRIS rather than Ilifu.")

    #add mutually exclusive group - don't want to build config, run pipeline, or display version at same time
    run_args = parser.add_mutually_exclusive_group(required=True)
    run_args.add_argument("-B","--build", action="store_true", required=False, default=False, help="Build config file using input MS.")
    run_args.add_argument("-R","--run", action="store_true", required=False, default=False, help="Run pipeline with input config file.")
    run_args.add_argument("-V","--version", action="store_true", required=False, default=False, help="Display the version of this pipeline and quit.")
    run_args.add_argument("-L","--license", action="store_true", required=False, default=False, help="Display this program's license and quit.")
        
    args, unknown = parser.parse_known_args()
        
    if len(unknown) > 0:
        parser.error('Unknown input argument(s) present - {0}'.format(unknown))
        
    if args.run:
        if args.config is None:
            parser.error("You must input a config file [--config] to run the pipeline.")
        if not os.path.exists(args.config):
            parser.error("Input config file '{0}' not found. Please set [-C --config] or write a new one with [-B --build].".format(args.config))

    #if user inputs a list a scripts, remove the default list
    if len(args.scripts) > len(globals.SCRIPTS):
        [args.scripts.pop(0) for i in range(len(globals.SCRIPTS))]
        if len(args.precal_scripts) > len(globals.PRECAL_SCRIPTS):
            [args.precal_scripts.pop(0) for i in range(len(globals.PRECAL_SCRIPTS))]
    if len(args.postcal_scripts) > len(globals.POSTCAL_SCRIPTS):
        [args.postcal_scripts.pop(0) for i in range(len(globals.POSTCAL_SCRIPTS))]
    
    #validate arguments before returning them
    validate_args(vars(args),args.config,parser=parser)

    return args


# ========================================================================================================

def parse_config(filename):
    """
    Given an input config file, parses it to extract key-value pairs that
    should represent task parameters and values respectively.
    """

    config = ConfigParser.SafeConfigParser(allow_no_value=True)
    config.read(filename)

    # Build a nested dictionary with tasknames at the top level
    # and parameter values one level down.
    taskvals = dict()
    for section in config.sections():

        if section not in taskvals:
            taskvals[section] = dict()

        for option in config.options(section):
            # Evaluate to the right type()
            try:
                taskvals[section][option] = ast.literal_eval(config.get(section, option))
            except (ValueError,SyntaxError):
                err = "Cannot format field '{0}' in config file '{1}'".format(option,filename)
                err += ", which is currently set to {0}. Ensure strings are in 'quotes'.".format(config.get(section, option))
                raise ValueError(err)

    return taskvals, config


# ========================================================================================================

def has_key(filename, section, key):
    config_dict,config = parse_config(filename)
    if has_section(filename, section) and key in config_dict[section]:
        return True
    return False


# ========================================================================================================

def has_section(filename, section):

    config_dict,config = parse_config(filename)
    return section in config_dict


# ========================================================================================================

def get_key(filename, section, key):
    config_dict,config = parse_config(filename)
    if has_key(filename, section, key):
        return config_dict[section][key]
    return ''


# ========================================================================================================

def remove_section(filename, section):

    config_dict,config = parse_config(filename)
    config.remove_section(section)
    config_file = open(filename, 'w')
    config.write(config_file)
    config_file.close()


# ========================================================================================================

def overwrite_config(filename, conf_dict={}, conf_sec='', sec_comment=''):

    config_dict,config = parse_config(filename)

    if conf_sec not in config.sections():
        logger.logger.debug('Writing [{0}] section in config file "{1}" with:\n{2}.'.format(conf_sec,filename,conf_dict))
        config.add_section(conf_sec)
    else:
        logger.logger.debug('Overwritting [{0}] section in config file "{1}" with:\n{2}.'.format(conf_sec,filename,conf_dict))

    if sec_comment != '':
        config.set(conf_sec, sec_comment)

    for key in conf_dict.keys():
        config.set(conf_sec, key, str(conf_dict[key]))

    config_file = open(filename, 'w')
    config.write(config_file)
    config_file.close()

def parse_spw(filename):

    config_dict,config = parse_config(filename)
    spw = config_dict['crosscal']['spw']
    nspw = config_dict['crosscal']['nspw']

    if ',' in spw:
        SPWs = spw.split(',')
        low,high,unit,dirs = [0]*len(SPWs),[0]*len(SPWs),['']*len(SPWs),['']*len(SPWs)
        for i,SPW in enumerate(SPWs):
            low[i],high[i],unit[i],func = processMeerKAT.get_spw_bounds(SPW)
            dirs[i] = '{0}~{1}{2}'.format(low[i],high[i],unit[i])

        lowest = min(low)
        highest = max(high)

        # Uncomment to use e.g. '*MHz'
        # if all([i == unit[0] for i in unit]):
        #     unit = unit[0]
        #     dirs = '*{0}'.format(unit)

    else:
        low,high,unit,func = processMeerKAT.get_spw_bounds(spw)
        dirs = []

    return low,high,unit,dirs


# ========================================================================================================

def validate_args(args,config,parser=None):
    
    """Validate arguments, coming from command line or config file. Raise relevant error (parser error or ValueError) if invalid argument found.
        
        Arguments:
        ----------
        args : dict
        Dictionary of slurm arguments from command line or config file.
        config : str
        Path to config file.
        parser : class ``argparse.ArgumentParser``, optional
        If this is input, parser error will be raised."""
    
    if parser is None or args['build']:
        if args['MS'] is None and not args['nofields']:
            msg = "You must input an MS [-M --MS] to build the config file."
            raise_error(config, msg, parser)
        
        if args['MS'] not in [None,'None'] and not os.path.isdir(args['MS']):
            msg = "Input MS '{0}' not found.".format(args['MS'])
            raise_error(config, msg, parser)

    if parser is not None and not args['build'] and args['MS']:
        msg = "Only input an MS [-M --MS] during [-B --build] step. Otherwise input is ignored."
        raise_error(config, msg, parser)
    
    if args['ntasks_per_node'] > globals.NTASKS_PER_NODE_LIMIT:
        msg = "The number of tasks per node [-t --ntasks-per-node] must not exceed {0}. You input {1}.".format(globals.NTASKS_PER_NODE_LIMIT,args['ntasks_per_node'])
        raise_error(config, msg, parser)
    
    if args['nodes'] > globals.TOTAL_NODES_LIMIT:
        msg = "The number of nodes [-N --nodes] per node must not exceed {0}. You input {1}.".format(globals.TOTAL_NODES_LIMIT,args['nodes'])
        raise_error(config, msg, parser)
    
    if args['mem'] > globals.MEM_PER_NODE_GB_LIMIT:
        if args['partition'] != 'HighMem':
            msg = "The memory per node [-m --mem] must not exceed {0} (GB). You input {1} (GB).".format(globals.MEM_PER_NODE_GB_LIMIT,args['mem'])
            raise_error(config, msg, parser)
        elif args['mem'] > globals.MEM_PER_NODE_GB_LIMIT_HIGHMEM:
            msg = "The memory per node [-m --mem] must not exceed {0} (GB) when using 'HighMem' partition. You input {1} (GB).".format(globals.MEM_PER_NODE_GB_LIMIT_HIGHMEM,args['mem'])
            raise_error(config, msg, parser)

    if args['plane'] > args['ntasks_per_node']:
        msg = "The value of [-P --plane] cannot be greater than the tasks per node [-t --ntasks-per-node] ({0}). You input {1}.".format(args['ntasks_per_node'],args['plane'])
        raise_error(config, msg, parser)
    
    if args['account'] not in ['b03-idia-ag','b05-pipelines-ag']:
        from platform import node
        if node() == 'slurm-login' or 'slwrk' in node():
            accounts=os.popen("for f in $(sacctmgr show user $(whoami) -s format=account%30 | grep -v 'Account\|--'); do echo -n $f,; done").read()[:-1].split(',')
            if args['account'] not in accounts:
                msg = "Accounting group '{0}' not recognised. Please select one of the following from your groups: {1}.".format(args['account'],accounts)
                raise_error(config, msg, parser)
        else:
            msg = "Accounting group '{0}' not recognised. You're not using a SLURM node, so cannot query your accounts.".format(args['account'])
            raise_error(config, msg, parser)

# ========================================================================================================

