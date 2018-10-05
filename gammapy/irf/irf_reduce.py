# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import, division, print_function, unicode_literals
from . import PSF3D, EnergyDependentTablePSF, IRFStacker
from ..utils.energy import Energy

__all__ = ["make_psf", "make_mean_psf", "make_mean_edisp"]


def make_psf(self, position, energy=None, rad=None):
    """Make energy-dependent PSF for a given source position.

    Parameters
    ----------
    position : `~astropy.coordinates.SkyCoord`
        Position at which to compute the PSF
    energy : `~astropy.units.Quantity`
        1-dim energy array for the output PSF.
        If none is given, the energy array of the PSF from the observation is used.
    rad : `~astropy.coordinates.Angle`
        1-dim offset wrt source position array for the output PSF.
        If none is given, the offset array of the PSF from the observation is used.

    Returns
    -------
    psf : `~gammapy.irf.EnergyDependentTablePSF`
        Energy dependent psf table
    """
    offset = position.separation(self.pointing_radec)

    if energy is None:
        energy = self.psf.to_energy_dependent_table_psf(theta=offset).energy

    if rad is None:
        rad = self.psf.to_energy_dependent_table_psf(theta=offset).rad

    if isinstance(self.psf, PSF3D):
        # PSF3D is a table PSF, so we use the native RAD binning by default
        # TODO: should handle this via a uniform caller API
        psf_value = self.psf.to_energy_dependent_table_psf(theta=offset).evaluate(
            energy
        )
    else:
        psf_value = self.psf.to_energy_dependent_table_psf(
            theta=offset, rad=rad
        ).evaluate(energy)

    arf = self.aeff.data.evaluate(offset=offset, energy=energy)
    exposure = arf * self.observation_live_time_duration

    psf = EnergyDependentTablePSF(
        energy=energy, rad=rad, exposure=exposure, psf_value=psf_value
    )
    return psf


def make_mean_psf(self, position, energy=None, rad=None):
    """Compute mean energy-dependent PSF.

    Parameters
    ----------
    position : `~astropy.coordinates.SkyCoord`
        Position at which to compute the PSF
    energy : `~astropy.units.Quantity`
        1-dim energy array for the output PSF.
        If none is given, the energy array of the PSF from the first
        observation is used.
    rad : `~astropy.coordinates.Angle`
        1-dim offset wrt source position array for the output PSF.
        If none is given, the energy array of the PSF from the first
        observation is used.

    Returns
    -------
    psf : `~gammapy.irf.EnergyDependentTablePSF`
        Mean PSF
    """
    psf = self[0].make_psf(position, energy, rad)

    if rad is None:
        rad = psf.rad
    if energy is None:
        energy = psf.energy

    exposure = psf.exposure
    psf_value = psf.psf_value.T * psf.exposure

    for obs in self[1:]:
        psf = obs.make_psf(position, energy, rad)
        exposure += psf.exposure
        psf_value += psf.psf_value.T * psf.exposure

    psf_value /= exposure
    psf_tot = EnergyDependentTablePSF(
        energy=energy, rad=rad, exposure=exposure, psf_value=psf_value.T
    )
    return psf_tot


def make_mean_edisp(
        self,
        position,
        e_true,
        e_reco,
        low_reco_threshold=Energy(0.002, "TeV"),
        high_reco_threshold=Energy(150, "TeV"),
):
    """Compute mean energy dispersion.

    Compute the mean edisp of a set of observations j at a given position

    The stacking is implemented in :func:`~gammapy.irf.IRFStacker.stack_edisp`

    Parameters
    ----------
    position : `~astropy.coordinates.SkyCoord`
        Position at which to compute the mean EDISP
    e_true : `~gammapy.utils.energy.EnergyBounds`
        True energy axis
    e_reco : `~gammapy.utils.energy.EnergyBounds`
        Reconstructed energy axis
    low_reco_threshold : `~gammapy.utils.energy.Energy`
        low energy threshold in reco energy, default 0.002 TeV
    high_reco_threshold : `~gammapy.utils.energy.Energy`
        high energy threshold in reco energy , default 150 TeV

    Returns
    -------
    stacked_edisp : `~gammapy.irf.EnergyDispersion`
        Stacked EDISP for a set of observation
    """
    list_aeff = []
    list_edisp = []
    list_livetime = []
    list_low_threshold = [low_reco_threshold] * len(self)
    list_high_threshold = [high_reco_threshold] * len(self)

    for obs in self:
        offset = position.separation(obs.pointing_radec)
        list_aeff.append(obs.aeff.to_effective_area_table(offset, energy=e_true))
        list_edisp.append(
            obs.edisp.to_energy_dispersion(offset, e_reco=e_reco, e_true=e_true)
        )
        list_livetime.append(obs.observation_live_time_duration)

    irf_stack = IRFStacker(
        list_aeff=list_aeff,
        list_edisp=list_edisp,
        list_livetime=list_livetime,
        list_low_threshold=list_low_threshold,
        list_high_threshold=list_high_threshold,
    )
    irf_stack.stack_edisp()

    return irf_stack.stacked_edisp