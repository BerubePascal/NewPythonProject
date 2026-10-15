"""
nicefigures

Helper functions for creating clean, publication-ready matplotlib figures.

Provides utilities to:
- Apply the static style in nice.mplstyle to new figures (use_style)
  or to existing axes (set_spines_linewidth, set_ticks_inside, enable_grid)
- Automatically extend axes to full ticks (even_ticks)
- Resize figures with single or double column widths using golden ratio (resize_figure)
- Do all of the above on a whole figure (apply_style)

Typical use:
    >>> import matplotlib.pyplot as plt
    >>> import nicefigures as nf
    >>> nf.use_style()              # optional, before creating figures
    >>> fig, ax = plt.subplots()
    >>> ax.plot([0, 1.3], [0, 2.7])
    >>> nf.apply_style(fig)         # after plotting; layout="double" for 18 cm

The style sheet ships with the package and can also be used on its own:
plt.style.use("nicefigures.nice").

Installed in every venv made by scaffold_project.py, in editable mode from
this repository: changes here apply to all projects at once.

Author: Pascal Bérubé
Date: 2025-08-22

Version: 2.0.0
Modifications:
- 2025-08-22: Initial version with even_ticks, set_spines_linewidth, and resize_figure functions.
- 2026-10-15: 2.0.0: packaged as src/nicefigures with pyproject.toml; static
  styling moved to nice.mplstyle (use_style); main renamed apply_style and
  applied to all axes (main kept as a deprecated alias); even_ticks skips
  non-linear axes and handles inverted axes; _snap_limits tolerance is
  relative to the tick spacing; removed dead code.
"""

import functools
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

STYLE_PATH = Path(__file__).with_name("nice.mplstyle")

FIGURE_WIDTHS_CM = {"single": 8.8, "double": 18.0}
GOLDEN_RATIO = 0.618


@functools.cache
def _style_params():
    """The settings in nice.mplstyle, read once."""
    return mpl.rc_params_from_file(STYLE_PATH, use_default_template=False)


def _style(key):
    """Read one value from nice.mplstyle."""
    return _style_params()[key]


def use_style() -> None:
    """
    Apply nice.mplstyle to all figures created afterwards.

    Examples
    --------
    >>> use_style()
    >>> fig, ax = plt.subplots()
    """
    plt.style.use(STYLE_PATH)


def _snap_limits(curr_min, curr_max, spacing):
    """
    Snap limits outward to the nearest multiples of spacing.

    A limit already on a multiple, up to floating-point noise, is kept rather
    than pushed out by a whole tick. The check is made on limit / spacing, so
    it works the same at any scale. Inverted limits (min > max) stay inverted.
    """
    if curr_min > curr_max:
        new_max, new_min = _snap_limits(curr_max, curr_min, spacing)
        return new_min, new_max

    def snap(value, outward):
        steps = value / spacing
        nearest = np.round(steps)
        if np.isclose(steps, nearest, rtol=0, atol=1e-6):
            return nearest * spacing
        return outward(steps) * spacing

    return snap(curr_min, np.floor), snap(curr_max, np.ceil)


def even_ticks(
    ax,
    axis: str = None,
    tick_spacing: float = None,
) -> None:
    """
    Adjust the axis limits to end on full ticks, respecting manual axis limits
    if set, and avoiding unnecessary extra ticks due to floating-point noise.

    Non-linear axes (log, symlog, ...) are left unchanged.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to adjust.
    axis : str, optional
        Which axis to adjust; must be 'x' or 'y'. If None, both axes are adjusted.
    tick_spacing : float, optional
        The spacing between major ticks. If None, the current tick interval is used.

    Raises
    ------
    ValueError
        If `axis` is not 'x', 'y', or None.
    """
    if axis not in ("x", "y", None):
        raise ValueError("axis must be 'x', 'y', or None")

    for ax_name in ["x", "y"] if axis is None else [axis]:
        # Select getter/setter functions dynamically
        if ax_name == "y":
            get_scale, get_lim, set_lim, get_ticks, set_locator = (
                ax.get_yscale,
                ax.get_ylim,
                ax.set_ylim,
                ax.get_yticks,
                ax.yaxis.set_major_locator,
            )
        else:
            get_scale, get_lim, set_lim, get_ticks, set_locator = (
                ax.get_xscale,
                ax.get_xlim,
                ax.set_xlim,
                ax.get_xticks,
                ax.xaxis.set_major_locator,
            )

        # Evenly spaced ticks only make sense on a linear axis
        if get_scale() != "linear":
            continue

        # Current limits (manual or auto)
        curr_min, curr_max = get_lim()

        # Compute tick spacing
        if tick_spacing is None:
            ticks = get_ticks()
            if len(ticks) > 1:
                axis_tick_spacing = ticks[1] - ticks[0]
            else:
                continue  # Skip adjustment if ticks are not meaningful
        else:
            axis_tick_spacing = tick_spacing

        # Snap to nearest valid ticks (avoids unwanted extra ticks)
        new_min, new_max = _snap_limits(curr_min, curr_max, axis_tick_spacing)

        # Apply new limits and locator
        set_lim(new_min, new_max)
        set_locator(MultipleLocator(axis_tick_spacing))


def enable_grid(ax) -> None:
    """
    Enable grid on the given Axes object with the style from nice.mplstyle.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to enable the grid on.
    """
    ax.grid(True, alpha=_style("grid.alpha"), linewidth=_style("grid.linewidth"))
    ax.set_axisbelow(True)  # Ensure grid is below the plot elements


def set_spines_linewidth(
    ax: plt.Axes,
    linewidth: float = None,
) -> None:
    """
    Set the line width of all four spines (top, bottom, left, right) of the given Axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object whose spines will be modified.
    linewidth : float, optional
        The desired line width for the spines (default: axes.linewidth from
        nice.mplstyle, 0.5).

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> set_spines_linewidth(ax, linewidth=0.8)
    """
    if linewidth is None:
        linewidth = _style("axes.linewidth")
    for spine in ax.spines.values():
        spine.set_linewidth(linewidth)


def set_ticks_inside(ax: plt.Axes, width: float = None, x_pad: float = None) -> None:
    """
    Move all ticks inside the plot, set their line width, and optionally adjust padding for x-axis labels.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object whose ticks will be modified.
    width : float, optional
        The desired width of the ticks (default: xtick.major.width from
        nice.mplstyle, 0.5).
    x_pad : float, optional
        Padding between x-axis labels and the x-axis spine. If None, default padding is used.

    Notes
    -----
    - Applies to both x and y axes.
    - Tick direction is set to 'in', and the width matches the spines.

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> set_ticks_inside(ax, width=0.5, x_pad=5)
    """
    if width is None:
        width = _style("xtick.major.width")
    ax.tick_params(
        axis="both",
        which="both",
        direction="in",
        width=width,
        top=True,
        bottom=True,
        left=True,
        right=True,
    )
    if x_pad is not None:
        ax.xaxis.set_tick_params(pad=x_pad)


def resize_figure(
    fig: plt.Figure,
    layout: str = "single",
    forward: bool = True,
) -> None:
    """
    Resize the figure automatically based on a predefined layout.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The Figure object to resize.
    layout : str, optional
        Either 'single' or 'double'. Determines the width of the figure.
        'single' -> width 8.8 cm, 'double' -> width 18.0 cm. Default is 'single'.
    forward : bool, optional
        If True, also resizes the canvas in GUI backends (default is True).

    Notes
    -----
    - Height is automatically set using the golden ratio: height = width * 0.618.
    - A figure already on screen is redrawn.

    Raises
    ------
    ValueError
        If layout is not 'single' or 'double'.

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> resize_figure(fig, layout='double')
    """
    if layout not in FIGURE_WIDTHS_CM:
        raise ValueError("layout must be 'single' or 'double'")

    width_cm = FIGURE_WIDTHS_CM[layout]
    height_cm = width_cm * GOLDEN_RATIO

    fig.set_size_inches(width_cm / 2.54, height_cm / 2.54, forward=forward)
    fig.canvas.draw_idle()


def apply_style(fig, axes=None, layout: str = "single") -> None:
    """
    Style a finished figure: thin spines, ticks inside, grid, limits on full
    ticks, and the single- or double-column size.

    Call it after plotting. Works whether or not use_style() was called.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The Figure to style and resize.
    axes : matplotlib.axes.Axes or iterable of Axes, optional
        The Axes to style. If None, all Axes of the figure.
    layout : str, optional
        Either 'single' or 'double'. Determines the width of the figure.
        'single' -> width 8.8 cm, 'double' -> width 18.0 cm. Default is 'single'.

    Examples
    --------
    >>> fig, (ax1, ax2) = plt.subplots(1, 2)
    >>> apply_style(fig, layout='double')
    """
    if axes is None:
        axes = fig.axes
    elif isinstance(axes, plt.Axes):
        axes = [axes]

    for ax in np.ravel(axes):
        set_spines_linewidth(ax)
        set_ticks_inside(ax, x_pad=_style("xtick.major.pad"))
        enable_grid(ax)
        even_ticks(ax)

    resize_figure(fig, layout)


def main(fig, ax, layout: str = "single") -> None:
    """Deprecated: use apply_style(fig, ax, layout)."""
    warnings.warn(
        "nicefigures.main is deprecated; use apply_style(fig, axes=None, layout=...)",
        DeprecationWarning,
        stacklevel=2,
    )
    apply_style(fig, ax, layout)
