"""
Runs dqa on the input MS
"""
import os,sys
sys.path.append(os.getcwd())

import os
import click
import glob
import pandas as pd

from utils import config_parser
from utils.config_parser import validate_args as va
from utils import globals
from utils import bookkeeping

from mightee_pol_dqa import cal as _cal
from mightee_pol_dqa import target as _target
from mightee_pol_dqa import backend


# --------------------------------------------------------------------------------------------------  

def get_imnames(impath, srclist):
    """
    Given the input image path and a list of source names, return the list of
    cubes and MFS images containing these sources.
    Inputs:
        impath      Input path containing the MFS images and cubes, string
        srclist     List of source names, list of str
    Returns:
        cube_list  List of cube image names with full path, list of str
        mfs_list   List of mfs image names with full path, list of str
    """

    cubes = glob.glob("*.cube.fits")
    mfs_images = glob.glob("*_IQUV*.fits")

    cube_list = []
    mfs_list = []

    for src in srclist:
        cube_count = 0
        mfs_count = 0
        for cube in cubes:
            if src in cube:
                cube_list.append(cube)
                cube_count += 1

        for mfs in mfs_images:
            if src in mfs:
                mfs_list.append(mfs)
                mfs_count += 1

        if cube_count == 0:
            logger.error(f'No cubes found for sources {src} in path {impath}.')
        if mfs_count == 0:
            logger.error(f'No MFS images found for sources {src} in path {impath}')
    
    cube_list = [os.path.join(impath, cc) for cc in cube_list]
    mfs_list  = [os.path.join(impath, cc) for cc in mfs_list]

    logging.info(f"Found the following cubes for source(s) {','.join(srclist)} {','.join(cube_list)}")
    logging.info(f"Found the following MFS images for source(s) {','.join(srclist)} {','.join(mfs_list)}")

    return cube_list, mfs_list
  
# --------------------------------------------------------------------------------------------------  
  
def split_cal_targets(images):
    """
    Split out list of calibrators and targets
    """

    cal_list = []
    cal_names = []
    target_list = []
    target_names = []
    obs_prefix = []

    for imname in images:
        srcname = imname.split('_')[3].split('.')[0]
        obs = imname.split('_')[:2]
        obs = "_".join(obs)
        obs_prefix.append(obs)

        for srcname in _cal.NAMES_3C286 + _cal.NAMES_3C138 + _cal.NAMES_J1939 + _cal.NAMES_J0408:
            if srcname in imname:
                cal_list.append(imname)
                cal_names.append(srcname)
                break

        target_list.append(imname)
        target_names.append(srcname)

    logger.info("Found the following calibrators : ", end="")
    logger.info(",".join(cal_names))

    logger.info("Found the following target : ", end="")
    logger.info(",".join(target_names))

    return cal_list, cal_names, target_list, target_names, obs_prefix

  
# --------------------------------------------------------------------------------------------------  

def cal_spectrum(fitscube, srcname, outpath=None, outprefix=None):
    """
    Given an input FITS cube and the source name, plots the full Stokes spectrum of the calibrator.
    When applicable, the Perley-Butler Stokes I and polarization models are over-plotted.
    If the models do not exist, only the measured spectra are plotted.
    Stokes I models exist for : 3C286, 3C138, J0408-6545 and J1939-6342
    Full Stokes models exist for : 3C286, 3C138
    """

    if outprefix is not None:
        savename_I = '%s_%s_StokesI.pdf'  % (outprefix, srcname)
        savename_QUV = '%s_%s_StokesQUV.pdf'  % (outprefix, srcname)
    else:
        print("Warning : No name prefix given. Will save as StokesI.pdf and StokesQUV.pdf")
        savename_I = 'StokesI.pdf'
        savename_QUV = 'StokesQUV.pdf'  % (outprefix, srcname)

    if outpath is not None:
        savename_I = os.path.join(outpath, savename_I)
        savename_QUV = os.path.join(outpath, savename_QUV)

    sI, sQ, sU, sV, freq = backend.grab_cube_data(fitscube)

    if srcname in _cal.NAMES_3C138:
        sI_model, sI_model_freqs = _cal.get_3C138_stokesI_model(freq)
        sQ_model, sU_model, model_freqs = _cal.calibrator_pol_poly(srcname, freq)
    elif srcname in _cal.NAMES_3C286:
        sI_model, sI_model_freqs = _cal.get_3C286_stokesI_model(freq)
        sQ_model, sU_model, model_freqs = _cal.calibrator_pol_poly(srcname, freq)
    elif srcname in _cal.NAMES_J1939:
        sI_model, sI_model_freqs = _cal.get_J1939_model(freq)
        sQ_model, sU_model, model_freqs = None, None, None
    elif srcname in _cal.NAMES_J0408:
        sI_model, sI_model_freqs = _cal.get_J0408_model(freq)
        sQ_model, sU_model, model_freqs = None, None, None

    backend.plot_stokesI_model(freq, sI, sI_model_freqs, sI_model, title='%s Stokes I Spectrum' % srcname, outname=savename_I)

    backend.plot_stokesQUV_model(freq, sQ, sU, sV, sQ_model, sU_model, model_freqs,
                                     title=r'%s Fractional Q, U \& V Spectrum' % srcname, outname=savename_QUV)

    return
  
# --------------------------------------------------------------------------------------------------  

def main(args,taskvals):

    """
    Run the mightee-pol DQA routines on all the data products for the input OBS_ID.
    This assumes a standard set of data products, such as the cubes from the
    calibrators and targets, as well as MFS images of the target and associated
    pyBDSF catalogs.
    It pulls the observation details from the obs_details.txt file located in
    
    /idia/projects/mightee/mightee-pol/scripts/wrappers/obs_details.txt
    It recognizes the following calibrators :\n
    * J1939-6342 - Unpolarized model\n
    * J0408-6545 - Unpolarized model\n
    * 3C138 - Full Stokes model\n
    * 3C286 - Full Stokes model\n
    * 3C48  - Full Stokes model\n
    Any calibrators not in the above list will be treated as secondary
    calibrators without a standard model. The calibrator spectrum will still be
    generated, but not a model spectrum
    """

    cwd = os.getcwd()
    impath = '/idia/projects/mightee/mightee-pol/processed/images/'

    df = pd.read_csv(OBS_DETAILS, delim_whitespace=True, header=None, comment='#')

    df.columns=['obs_date', 'obs_id', 'pointing', 'target', 'primary',
                'secondary', 'other_cal', 't_int', 'chan', 't_tot', 't_on', 'Nant']

    sdf = df[df['obs_id'] == obs_id]
    pointing = sdf['pointing'].values[0]
    obs_suffix = f'{pointing}_{obs_id}'

    # Get the full pathname
    impath = os.path.join(impath, obs_suffix)

    if not os.path.exists(impath):
        raise OSError(f'Path to directory {impath} does not exist. Please double check your inputs.')

    os.chdir(impath)

    # There could be multiple primaries and other_cals so split on , 
    # pol cals will most likely  be in other_cal
    # The split() call also guarantees this will always be iterable lists.
    primary = sdf['primary'].values[0].split(',')
    secondary = sdf['secondary'].values[0].split(',')
    other_cal = sdf['other_cal'].values[0].split(',')
    target = sdf['target'].values[0].split(',')

    cube_primary, mfs_primary = get_imnames(impath, primary)
    cube_secondary, mfs_secondary = get_imnames(impath, secondary)
    cube_other_cal, mfs_other_cal = get_imnames(impath, other_cal)
    cube_target, mfs_target = get_imnames(impath, target)

    #cal_cubes, cal_cube_names, target_cubes, target_cube_names, obs_prefix = split_cal_targets(cubes)
    ## Technically cubes, since they still have 4 Stokes planes
    #cal_ims, cal_im_names, target_ims, target_im_names, obs_prefix = split_cal_targets(mfs_images)

    #for calcube, calname, obs in zip(cal_cubes, cal_cube_names, obs_prefix):
    #    print("Processing %s %s" % (obs, calname))
    #    cal_spectrum(calcube, calname, outpath=cwd, outprefix=obs)

    os.chdir(cwd)
    
    config_parser.overwrite_config(args['config'], conf_sec='data', conf_dict={'vis':mvis})
    config_parser.overwrite_config(args['config'], conf_sec='run', sec_comment='# Internal variables for pipeline execution', conf_dict={'orig_vis':vis})
    msmd.done()

    return
  
# --------------------------------------------------------------------------------------------------  
# --------------------------------------------------------------------------------------------------  

if __name__ == '__main__':

    bookkeeping.run_script(main)
