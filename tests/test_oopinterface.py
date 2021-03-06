import os
import numpy as np
from math import pi
from scipy.interpolate import interp1d

from hn2016_falwa.constant import *
from hn2016_falwa.oopinterface import QGField

# === Parameters specific for testing the qgfield class ===
nlev = 12
nlat = 31
nlon = 60
xlon = np.linspace(0, 2. * pi, nlon, endpoint=False)
ylat = np.linspace(-90., 90., nlat, endpoint=True)
plev = np.array([1000, 900, 800, 700, 600, 500, 400, 300, 200, 100, 10, 1])
kmax = 49
get_cwd = os.path.dirname(os.path.abspath(__file__))
u_field = np.reshape(np.loadtxt(get_cwd + '/test_data/demo_u.txt'), [nlev, nlat, nlon])
v_field = np.reshape(np.loadtxt(get_cwd + '/test_data/demo_u.txt'), [nlev, nlat, nlon])
t_field = np.reshape(np.loadtxt(get_cwd + '/test_data/demo_u.txt'), [nlev, nlat, nlon])
theta_field = t_field * (plev[:, np.newaxis, np.newaxis] / P0) ** (-DRY_GAS_CONSTANT / CP)


def test_qgfield():

    # Create a QGField object for testing
    qgfield = QGField(
        xlon=xlon,
        ylat=ylat,
        plev=plev,
        u_field=u_field,
        v_field=v_field,
        t_field=t_field,
        kmax=kmax,
        maxit=100000,
        dz=1000.,
        prefactor=6500.,
        npart=None,
        tol=1.e-5,
        rjac=0.95,
        scale_height=SCALE_HEIGHT,
        cp=CP,
        dry_gas_constant=DRY_GAS_CONSTANT,
        omega=EARTH_OMEGA,
        planet_radius=EARTH_RADIUS
    )

    # Check that the input fields are interpolated onto a grid of correct dimension
    # and the interpolated values are bounded.
    qgpv, interpolated_u, interpolated_v, interpolated_theta, static_stability = \
        qgfield.interpolate_fields()

    # Check that the dimensions of the interpolated fields are correct
    assert (49, 31, 60) == qgpv.shape
    assert (49, 31, 60) == interpolated_u.shape
    assert (49, 31, 60) == interpolated_v.shape
    assert (49, 31, 60) == interpolated_theta.shape
    assert (49,) == static_stability.shape

    assert (interpolated_u[1:-1, :, :].max() <= u_field.max()) & \
           (interpolated_u[1:-1, :, :].max() >= u_field.min())
    assert (interpolated_u[1:-1, :, :].min() <= u_field.max()) & \
           (interpolated_u[1:-1, :, :].min() >= u_field.min())
    assert (interpolated_v[1:-1, :, :].max() <= v_field.max()) & \
           (interpolated_v[1:-1, :, :].max() >= v_field.min())
    assert (interpolated_v[1:-1, :, :].min() <= v_field.max()) & \
           (interpolated_v[1:-1, :, :].min() >= v_field.min())
    assert (interpolated_theta[1:-1, :, :].max() <= theta_field.max()) & \
           (interpolated_theta[1:-1, :, :].max() >= theta_field.min())
    assert (interpolated_theta[1:-1, :, :].min() <= theta_field.max()) & \
           (interpolated_theta[1:-1, :, :].min() >= theta_field.min())
    assert 0 == np.isnan(qgpv).sum()
    assert 0 == (qgpv == float('Inf')).sum()

    # Check that the output reference states are of correct dimension, and
    # the QGPV reference state is non-decreasing.
    qref_north_hem, uref_north_hem, ptref_north_hem = \
        qgfield.compute_reference_states(
            northern_hemisphere_results_only=True
        )

    # Check dimension of the input field
    assert (49, 16) == qref_north_hem.shape
    assert (49, 16) == uref_north_hem.shape
    assert (49, 16) == ptref_north_hem.shape
    assert (np.diff(qref_north_hem, axis=-1)[:, :] >= 0.).all()
    return None


def test_interpolate_fields_even_grids():
    """
    To test whether the new features of even-to-odd grid interpolation works well.

    .. versionadded:: 0.3.5

    """
    ylat_even = np.linspace(-90., 90., nlat + 1, endpoint=True)[1:-1]
    u_field_even = interp1d(ylat, u_field, axis=1,
                            fill_value="extrapolate")(ylat_even)
    v_field_even = interp1d(ylat, v_field, axis=1,
                            fill_value="extrapolate")(ylat_even)
    t_field_even = interp1d(ylat, t_field, axis=1,
                            fill_value="extrapolate")(ylat_even)

    # Create a QGField object for testing
    qgfield_even = QGField(
        xlon=xlon,
        ylat=ylat_even,
        plev=plev,
        u_field=u_field_even,
        v_field=v_field_even,
        t_field=t_field_even,
        kmax=kmax,
        maxit=100000,
        dz=1000.,
        prefactor=6500.,
        npart=None,
        tol=1.e-5,
        rjac=0.95,
        scale_height=SCALE_HEIGHT,
        cp=CP,
        dry_gas_constant=DRY_GAS_CONSTANT,
        omega=EARTH_OMEGA,
        planet_radius=EARTH_RADIUS
    )

    qgpv, interpolated_u, interpolated_v, interpolated_theta, static_stability = \
        qgfield_even.interpolate_fields()

    assert 49 == qgfield_even.kmax
    assert 30 == qgfield_even.get_latitude_dim()
    assert 60 == qgfield_even.nlon

    # Check that the dimensions of the interpolated fields are correct
    assert (49, 30, 60) == qgpv.shape
    assert (49, 30, 60) == interpolated_u.shape
    assert (49, 30, 60) == interpolated_v.shape
    assert (49, 30, 60) == interpolated_theta.shape
    assert (49,) == static_stability.shape

    # Check that at the interior grid points, the interpolated fields
    # are bounded
    assert (interpolated_u[1:-1, 1:-1, 1:-1].max() <= u_field.max()) & \
           (interpolated_u[1:-1, 1:-1, 1:-1].max() >= u_field.min())

    assert (interpolated_u[1:-1, 1:-1, 1:-1].min() <= u_field.max()) & \
           (interpolated_u[1:-1, 1:-1, 1:-1].min() >= u_field.min())

    assert (interpolated_v[1:-1, 1:-1, 1:-1].max() <= v_field.max()) & \
           (interpolated_v[1:-1, 1:-1, 1:-1].max() >= v_field.min())

    assert (interpolated_v[1:-1, 1:-1, 1:-1].min() <= v_field.max()) & \
           (interpolated_v[1:-1, 1:-1, 1:-1].min() >= v_field.min())

    assert (interpolated_theta[1:-1, 1:-1, 1:-1].max() <= theta_field.max()) & \
           (interpolated_theta[1:-1, 1:-1, 1:-1].max() >= theta_field.min())

    assert (interpolated_theta[1:-1, 1:-1, 1:-1].min() <= theta_field.max()) & \
           (interpolated_theta[1:-1, 1:-1, 1:-1].min() >= theta_field.min())

    assert 0 == np.isnan(qgpv).sum()
    assert 0 == (qgpv == float('Inf')).sum()

