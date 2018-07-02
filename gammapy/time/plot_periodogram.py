# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np

__all__ = [
    'plot_periodogram',
]


def plot_periodogram(time, flux, periods, power, flux_err=np.array([None]), best_period=None, fap=None):
    """
    Plots a light curve and its periodogram.

    The highest period of the periodogram and its false alarm probability (FAP) will be added to the plot, if given.
    If multiple FAPs are forwarded, the lowest one will be used.

    Parameters
    ----------
    time : `~numpy.ndarray`
        Time array of the light curve
    flux : `~numpy.ndarray`
        Flux array of the light curve
    periods : `~numpy.ndarray`
        Periods for the periodogram
    power : `~numpy.ndarray`
        Periodogram peaks of the data
    flux_err : `~numpy.ndarray` (optional, default=np.zeros_like(flux))
        Flux error array of the light curve
    best_period : `float` (optional, default=None)
        Highest period of the periodogram
    fap : `float` (optional, default=None)
        False alarm probability of ``best_period`` under the specified significance criterion.

    Returns
    -------
    fig : `~matplotlib.figure.Figure`
        Matplotlib figure
    """
    # set flux errors
    if flux_err.any() == None:
        flux_err = np.ones_like(flux)

    # start plot
    import matplotlib.pyplot as plt

    # set up the figure & axes for plotting
    fig = plt.figure(figsize=(16, 9))
    grid_spec = plt.GridSpec(2, 1)

    # plot the light curve
    ax = fig.add_subplot(grid_spec[0, :])
    ax.errorbar(time, flux, flux_err, fmt='ok', label='light curve', elinewidth=1.5, capsize=0)
    ax.set_xlabel('time')
    ax.set_ylabel('flux')
    # ax.set_xlim(np.min(time), np.max(time))
    ax.legend()

    # plot the periodogram
    ax = fig.add_subplot(grid_spec[1, :])
    ax.plot(periods, power, c='k', label='periodogram')
    # mark the best period and label with significance
    if best_period is not None:
        if fap is None:
            raise ValueError('Must give a false alarm probability if you give a best_period')

        # set precision for period format
        pre = int(abs(np.floor(np.log10(np.max(np.diff(periods))))))
        label = 'Detected period p = {:.{}f} with {:.2E} FAP'.format(best_period, pre, fap)
        ymax = power[periods == best_period]
        ax.axvline(best_period, ymin=0, ymax=ymax, label=label, c='r')

    ax.set_xlabel('period')
    ax.set_ylabel('power')
    ax.set_xlim(0, np.max(periods))
    ax.legend()

    return fig
