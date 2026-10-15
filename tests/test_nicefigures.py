import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import nicefigures as nf


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")
    plt.rcdefaults()


@pytest.mark.parametrize(
    "limits, spacing, expected",
    [
        ((0.0, 0.9), 0.2, (0.0, 1.0)),
        ((0.1 + 0.2, 1.0), 0.1, (0.3, 1.0)),  # 0.30000000000000004 is on a tick
        ((-0.05, 0.95), 0.1, (-0.1, 1.0)),
        ((3e-9, 1.05e-7), 1e-8, (0.0, 1.1e-7)),  # small scale
        ((-3e-8, 1e-7 + 1e-22), 1e-8, (-3e-8, 1e-7)),  # upper bound on a tick
        ((2e6, 7.3e6), 1e6, (2e6, 8e6)),  # large scale
        ((1.0, -0.15), 0.5, (1.0, -0.5)),  # inverted axis
    ],
)
def test_snap_limits(limits, spacing, expected):
    assert np.allclose(nf._snap_limits(*limits, spacing), expected, rtol=1e-12, atol=0)


def test_apply_style_all_axes():
    fig, axes = plt.subplots(2, 2)
    x = np.linspace(0.13, 9.7, 50)
    for ax in axes.flat:
        ax.plot(x, x**2)
    axes[0, 1].set_yscale("log")
    axes[1, 0].invert_xaxis()
    log_ylim = axes[0, 1].get_ylim()

    nf.apply_style(fig, layout="double")

    assert axes[0, 1].get_ylim() == log_ylim  # log axis left alone
    assert axes[1, 0].xaxis_inverted()
    for ax in axes.flat:
        lo, hi = ax.get_xlim()
        step = ax.get_xticks()[1] - ax.get_xticks()[0]
        assert np.isclose(lo / step, round(lo / step))
        assert np.isclose(hi / step, round(hi / step))
        assert ax.spines["top"].get_linewidth() == 0.5
    assert np.allclose(fig.get_size_inches() * 2.54, (18.0, 18.0 * 0.618))


def test_apply_style_single_axes_only():
    fig, (ax1, ax2) = plt.subplots(1, 2)
    nf.apply_style(fig, ax1)
    assert ax1.spines["top"].get_linewidth() == 0.5
    assert ax2.spines["top"].get_linewidth() != 0.5


def test_main_is_deprecated_alias():
    fig, ax = plt.subplots()
    ax.plot([0, 1.3], [0, 2.7])
    with pytest.warns(DeprecationWarning):
        nf.main(fig, ax)
    assert ax.get_ylim() == (-0.5, 3.0)


def test_use_style_applies_to_new_figures():
    nf.use_style()
    fig, _ = plt.subplots()
    assert np.isclose(fig.get_size_inches()[0] * 2.54, 8.8, atol=0.01)
    assert plt.rcParams["xtick.direction"] == "in"
    assert plt.rcParams["axes.grid"]


def test_style_sheet_ships_with_package():
    assert nf.STYLE_PATH.is_file()
    plt.style.use("nicefigures.nice")  # dotted name: matplotlib >= 3.7
    assert plt.rcParams["axes.linewidth"] == 0.5


def test_resize_figure_rejects_unknown_layout():
    fig, _ = plt.subplots()
    with pytest.raises(ValueError):
        nf.resize_figure(fig, "triple")
