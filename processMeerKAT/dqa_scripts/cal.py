#!/usr/bin/env python3

import numpy as np

NAMES_3C138 = ["3C138", "0518+165", "0521+166", "J0521+1638"]
NAMES_3C286 = ["3C286", "1328+307", "1331+305", "J1331+3030"]
NAMES_3C48  = ["3C48", "0134+329", "0137+331", "J0137+3309"]
NAMES_J1939 = ['J1939-6342', 'B1934-638', '1934-638', '1939-6342']
NAMES_J0408 = ['J0408-6545', '0408-6546']

def get_J1939_model(freqs):
    """
    Return the polynomial model of J1939 generated over the given
    frequencies.
    """

    # Freq in MHz
    freqs /= 1e6
    model_freqs = np.linspace(freqs.min(), freqs.max(), 4000)
    freqs *= 1e6 # Undo what we did before

    f_coeff=[-30.7667,26.4908,-7.0977,0.605334]   # From ATCA Calibrator database
    logS = f_coeff[0] + f_coeff[1]*np.log10(model_freqs) + f_coeff[2]*np.log10(model_freqs)**2 + f_coeff[3]*np.log10(model_freqs)**3

    return 10.0**logS, model_freqs*1e6


def get_J0408_model(freqs):
    """
    Return the polynomial model of J1939 generated over the given
    frequencies.
    """

    # Freq in MHz
    freqs /= 1e6
    model_freqs = np.linspace(freqs.min(), freqs.max(), 4000)
    freqs *= 1e6 # Undo what we did before

    # From SARAO
    ref_flux = 17.066
    spix = -1.179
    reffreq = 1284 # MHz

    flux = ref_flux * (freqs/reffreq)**spix

    return flux, model_freqs*1e6



def get_3C138_stokesI_model(freqs):
    """
    Return the polynomial model of 3C138 generated over the given
    frequencies.
    """

    # Freq in GHz
    freqs /= 1e9
    model_freqs = np.linspace(freqs.min(), freqs.max(), 4000)
    freqs *= 1e9

    f_coeff = [1.0088, -0.4981, -0.1552, -0.0102, 0.0223] # From Perley-Butler 2013

    logS = f_coeff[0] + f_coeff[1]*np.log10(model_freqs) + f_coeff[2]*(np.log10(model_freqs))**2 + f_coeff[3]*(np.log10(model_freqs))**3 +\
          f_coeff[4]*(np.log10(model_freqs))**4

    return 10.0**logS, model_freqs*1e9



def get_3C286_stokesI_model(freqs):
    """
    Return the polynomial model of 3C138 generated over the given
    frequencies.
    """

    # Freq in GHz
    freqs /= 1e9
    model_freqs = np.linspace(freqs.min(), freqs.max(), 4000)
    freqs *= 1e9

    f_coeff = [1.2481, -0.4507, -0.1798, 0.0357] # From Perley-Butler 2013

    logS = f_coeff[0] + f_coeff[1]*np.log10(model_freqs) + f_coeff[2]*(np.log10(model_freqs))**2 + f_coeff[3]*(np.log10(model_freqs))**3


    return 10.0**logS, model_freqs*1e9



def calibrator_pol_poly(srcname, freqs, deg=3):
    """
    Return the polarization polynomials fitted to the known standard calibrator
    measurements.
    """

    # Freqs in GHz
    freqs /= 1e9
    model_freqs = np.linspace(freqs.min(), freqs.max(), 4000)
    freqs *= 1e9

    freqvals = [1.050, 1.450, 1.640, 1.950]

    if srcname in NAMES_3C48:
        pvals = np.asarray([0.3, 0.5, 0.7, 0.9])/100.
        chivals = [25, 140, -5, -150]
    elif srcname in NAMES_3C138:
        pvals = np.asarray([5.6, 7.5, 8.4, 9.0])/100.
        chivals = [-14, -11, -10, -10]
    elif srcname in NAMES_3C286:
        pvals = np.asarray([8.6, 9.5, 9.9, 10.1])/100.
        chivals = [33, 33, 33, 33]

    pcoeffs = np.polyfit(freqvals, pvals, deg=deg)
    chicoeffs = np.polyfit(freqvals, chivals, deg=deg)

    ppoly = np.poly1d(pcoeffs)
    chipoly = np.poly1d(chicoeffs)

    fracQ = ppoly(model_freqs) * np.cos(2*np.deg2rad(chipoly(model_freqs)))
    fracU = ppoly(model_freqs) * np.sin(2*np.deg2rad(chipoly(model_freqs)))

    return fracQ, fracU, model_freqs*1e9
