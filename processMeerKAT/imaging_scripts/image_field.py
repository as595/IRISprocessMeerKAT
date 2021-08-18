# [210818 - AMS] Script created

import sys
import glob
import os

import config_parser
from config_parser import validate_args as va
import bookkeeping

from casatasks import *
logfile=casalog.logfile()
#casalog.setlogfile('logs/{SLURM_JOB_NAME}-{SLURM_JOB_ID}.casa'.format(**os.environ))
import casampi

import logging
from time import gmtime
logging.Formatter.converter = gmtime
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)-15s %(levelname)s: %(message)s", level=logging.INFO)

# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------

targetname = 'COSMOS'

ImageParams = namedtuple('ImageParams', ['niter', 'threshold', 'imsize', 'wprojplanes', 'datacolumn', 'gridder', 'cell', 'pol'])
pol = 'IQUV'
impars_target = ImageParams(100000, '0.04mJy', 6144, 768, 'data', 'wproject', '1.5arcsec', pol)
impars_cal = ImageParams(2000, '1.0mJy', 512, 64, 'data', 'standard', '1.5arcsec', pol)

# --------------------------------------------------------------------------------------------------------------------------------

def get_imname(vis):
  
  if vis.find('.mms')>0:
    # .mms
    imagename = vis[:-4]
  else:
    # .ms
    imagename = vis[:-3]
    
  return imagename

# --------------------------------------------------------------------------------------------------------------------------------

def image_cal(vis):
  
    imagename = get_imname(vis)
    
    tclean(vis=vis, field='', datacolumn=impars_cal.datacolumn, imagename=imagename,
        imsize=impars_cal.imsize, cell=impars_cal.cell, stokes=impars_cal.pol, gridder=impars_cal.gridder,
        wprojplanes = impars_cal.wprojplanes, deconvolver = 'mtmfs', restoration=True,
        weighting='briggs', robust = 0.0, niter=impars_cal.niter,
        threshold=impars_cal.threshold, nterms=2, parallel = True)
    
    statname = imagename+'.image.tt0'
    fitsname = imagename+'.image.fits'
    exportfits(imagename=statname, fitsimage=fitsname, overwrite=True)
    
    return

# --------------------------------------------------------------------------------------------------------------------------------

def image_target(vis):
  
    imagename = get_imname(vis)
    
    for robust in [-0.5,0.4]:
      
        tclean(vis=vis, field='', datacolumn=impars_target.datacolumn, imagename=imagename,
            imsize=impars_target.imsize, cell=impars_target.cell, stokes=impars_target.pol, gridder=impars_target.gridder,
            wprojplanes = impars_target.wprojplanes, deconvolver = 'mtmfs', restoration=True,
            weighting='briggs', robust = robust, niter=impars_target.niter,
            threshold=impars_target.threshold, nterms=2, parallel = True)

        statname = imagename+'.'+str(robust)+'.image.tt0'
        fitsname = imagename+'.'+str(robust)+'.image.fits'
        exportfits(imagename=statname, fitsimage=fitsname, overwrite=True)

    return

# --------------------------------------------------------------------------------------------------------------------------------

def main():

  visname = va(taskvals, 'data', 'vis', str)
    
  if visname.find(targetname)>0:
    image_target(visname)
  else:
    image_cal(visname)
  return
  
# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    bookkeeping.run_script(main,logfile)
