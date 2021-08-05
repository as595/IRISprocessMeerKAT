#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord

import matplotlib.pyplot as plt
import matplotlib.cm as cm

plt.style.use('seaborn-poster')


def set_plotstyles(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return ax


def grab_cube_data(fitscube, pixX=None, pixY=None):
    """
    Returns the I, frac Q, U, & V and frequency values from the central pixel of the given FITS cube.
    By default it will pull from the central pixel, but any (X,Y) pixel can be specified.
    """
    if not os.path.exists(fitscube):
        raise FileNotFoundError(f'FITS cube {fitscube} does not exist.')

    with fits.open(fitscube, memmap=True) as ffile:
        imgdat = ffile[0].data
        shape = imgdat.shape
        nchan = shape[1]

        cx, cy = shape[2]//2, shape[3]//2

        if pixX is None:
            pixX = cx
        if pixY is None:
            pixY = cy

        freq0 = ffile[0].header['CRVAL3']
        freqdelt = ffile[0].header['CDELT3']
        refpix = ffile[0].header['CRPIX3']

        freq0 = freq0 - freqdelt*refpix

        # In Hz
        freqspec  = np.linspace(freq0, freq0+nchan*freqdelt, nchan)
        Ispec     = imgdat[0, :, pixY, pixX]
        fracQspec = imgdat[1, :, pixY, pixX]/Ispec
        fracUspec = imgdat[2, :, pixY, pixX]/Ispec
        fracVspec = imgdat[3, :, pixY, pixX]/Ispec

    return Ispec, fracQspec, fracUspec, fracVspec, freqspec



def get_fits_iquv(fitsnames, do_rotate=True, rotate_file_path='/idia/projects/mightee/mightee-pol/processed/cube_rotation_angles.txt',
                                                    filter_by_med=True):
    """
    Given a list of FITS cubes, returns a list of frequencies and IQUV values for each cube
    """

    freqs = []
    Is = []
    fracQs = []
    fracUs = []
    fracVs = []

    for ff in fitsnames:
        if not os.path.exists(ff):
            print(f"Warning : {ff} does not exist. Skipping.")
            continue

        Ispec, fracQspec, fracUspec, fracVspec, freqspec = grab_cube_data(ff)

        if do_rotate:
            skipthis, fracQ, fracU, fracV = rotate_spectra(ff, fracQspec, fracUspec, fracVspec, freqspec, rotate_file_path)

            if skipthis:
                print(f"Warning : No rotation information found for {ff}. Skipping.")
                continue

            fracQs.append(fracQ)
            fracUs.append(fracU)
            fracVs.append(fracV)
        else:
            fracQs.append(fracQspec)
            fracUs.append(fracUspec)
            fracVs.append(fracVspec)

        freqs.append(freqspec/1e9)
        Is.append(Ispec)

    # Reject cubes that are of a different size to the median size. This is a simple way to
    # reject cubes with many missing channels or a different resolution. This will reject also cubes with the same resolution
    # but a different total bandwidth.
    if filter_by_med:
        medsize = np.median([ff.size for ff in freqs])
        freqs = [ff for ff in freqs if ff.size == medsize]
        Is = [ff for ff in Is if ff.size == medsize]
        fracQs = [ff for ff in fracQs if ff.size == medsize]
        fracUs = [ff for ff in fracUs if ff.size == medsize]
        fracVs = [ff for ff in fracVs if ff.size == medsize]

    return freqs, Is, fracQs, fracUs, fracVs


def plot_stokesI_model(meas_freq, meas_specI, model_freq, model_specI, title=None, outname=None):
    """
    Given the input arrays containing the measured spectrum and model specrum,
    generates the plot.
    """

    fig, ax = plt.subplots(figsize=(14,10))
    ax = set_plotstyles(ax)

    ax.scatter(meas_freq/1e9, meas_specI, color='tab:blue', label='Measured', alpha=0.8)
    ax.plot(model_freq/1e9, model_specI, color='tab:orange', label='Model')

    plt.legend()

    if title is not None:
        ax.set_title(title)

    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('Flux Density (Jy)')

    if outname is not None:
        if 'pdf' not in outname:
            outname += '.pdf'
        plt.savefig(outname, bbox_inches='tight')



def plot_stokesQUV_model(meas_freq, meas_specQ, meas_specU, meas_specV, model_specQ, model_specU, model_freq, title=None, outname=None):
    """
    Plots the measured fractional Stokes-Q, -U and -V without over-plotting the
    model. Useful to check residual polarization on unpolarized calibrators like
    J1939.
    """

    fig, ax = plt.subplots(figsize=(14,10))
    ax = set_plotstyles(ax)

    ax.scatter(meas_freq/1e9, meas_specQ, color='tab:blue', label='Measured Frac. Q', alpha=0.8)
    ax.scatter(meas_freq/1e9, meas_specU, color='tab:orange', label='Measured Frac. U', alpha=0.8)
    ax.scatter(meas_freq/1e9, meas_specV, color='tab:green', label='Measured Frac. V', alpha=0.8)

    if model_specQ is not None:
        ax.plot(model_freq/1e9, model_specQ, color='tab:blue', label='Model Frac. Q', alpha=1.0)
        ax.plot(model_freq/1e9, model_specU, color='tab:orange', label='Model Frac. U', alpha=1.0)

    plt.legend()

    if title is not None:
        ax.set_title(title)

    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('Fractional Polarization')

    if outname is not None:
        if 'pdf' not in outname:
            outname += '.pdf'
        plt.savefig(outname, bbox_inches='tight')
