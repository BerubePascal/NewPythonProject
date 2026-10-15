"""
nicefigures.py

Helper functions for creating clean, publication-ready matplotlib figures.

Provides utilities to:
- Automatically extend axes to full ticks (even_ticks)
- Set spine line widths (set_spines_linewidth)
- Adjust tick position and width to match spines
- Resize figures with single or double column widths using golden ratio (resize_figure)

Author: Pascal Bérubé
Date: 2025-08-22

Version: 1.0
Modifications:
- 2025-08-22: Initial version with even_ticks, set_spines_linewidth, and resize_figure functions.
"""

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.ticker import MultipleLocator


# Helper to get min and max of data on the axis
def get_data_range(ax, axis):
    values = []

    for line in ax.get_lines():
        ydata, xdata = line.get_ydata(), line.get_xdata()
        values.append(ydata.max() if axis == "y" else xdata.max())
        values.append(ydata.min() if axis == "y" else xdata.min())

    for coll in ax.collections:  # scatter plots
        offsets = coll.get_offsets()
        if offsets.size > 0:
            values.append(offsets[:, 1].max() if axis == "y" else offsets[:, 0].max())
            values.append(offsets[:, 1].min() if axis == "y" else offsets[:, 0].min())

    if not values:
        raise ValueError(f"No data found on axis '{axis}'")
    return min(values), max(values)


# def even_ticks(
#     ax,
#     axis: str = None,
#     tick_spacing: float = None,
# ) -> None:
#     """
#     Adjust the axis limits to full ticks above and below the data range.


#     Parameters
#     ----------
#     ax : matplotlib.axes.Axes
#     The Axes object to adjust.
#     axis : str, optional
#     Which axis to adjust; must be 'x' or 'y'. If None, both axes are adjusted.
#     tick_spacing : float, optional
#     The spacing between major ticks. If None, the current tick interval is used.


#     Raises
#     ------
#     ValueError
#     If `axis` is not 'x', 'y', or None, or if there is no data on the axis.


#     Notes
#     -----
#     - Call this function after plotting your data.
#     - Automatically detects scatter and line plots.
#     - If tick_spacing is None, it is computed from current ticks.


#     Examples
#     --------
#     >>> fig, ax = plt.subplots()
#     >>> ax.plot([1,2,3], [4,5,6])
#     >>> even_ticks(ax)
#     >>> even_ticks(ax, 'y')
#     """

#     axes_to_adjust = ["x", "y"] if axis is None else [axis]

#     for ax_name in axes_to_adjust:
#         if ax_name not in ["x", "y"]:
#             raise ValueError("axis must be 'x', 'y', or None")

#         data_min, data_max = get_data_range(ax, ax_name)

#         # Compute tick spacing **per axis**
#         if tick_spacing is None:
#             if ax_name == "y":
#                 ticks = ax.get_yticks()
#             else:
#                 ticks = ax.get_xticks()
#             axis_tick_spacing = ticks[1] - ticks[0]
#         else:
#             axis_tick_spacing = tick_spacing

#         new_min = axis_tick_spacing * np.floor(data_min / axis_tick_spacing)
#         new_max = axis_tick_spacing * np.ceil(data_max / axis_tick_spacing)

#         if ax_name == "y":
#             ax.set_ylim(new_min, new_max)
#             ax.yaxis.set_major_locator(MultipleLocator(axis_tick_spacing))
#         else:
#             ax.set_xlim(new_min, new_max)
#             ax.xaxis.set_major_locator(MultipleLocator(axis_tick_spacing))


def _snap_limits(curr_min, curr_max, spacing, tol=1e-9):
    """
    Snap limits outward to the nearest multiples of spacing,
    but avoid extending past an exact tick due to floating errors.
    """
    # Lower bound
    if abs(curr_min % spacing) < tol or abs(curr_min % spacing - spacing) < tol:
        new_min = curr_min  # already aligned to tick
    else:
        new_min = spacing * np.floor(curr_min / spacing)

    # Upper bound
    if abs(curr_max % spacing) < tol:
        new_max = curr_max
    else:
        new_max = spacing * np.ceil(curr_max / spacing)

    return new_min, new_max


def even_ticks(
    ax,
    axis: str = None,
    tick_spacing: float = None,
) -> None:
    """
    Adjust the axis limits to end on full ticks, respecting manual axis limits
    if set, and avoiding unnecessary extra ticks due to floating-point noise.

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

    axes_to_adjust = ["x", "y"] if axis is None else [axis]

    for ax_name in axes_to_adjust:
        if ax_name not in ["x", "y"]:
            raise ValueError("axis must be 'x', 'y', or None")

        # Select getter/setter functions dynamically
        if ax_name == "y":
            get_lim, set_lim, get_ticks, set_locator = (
                ax.get_ylim,
                ax.set_ylim,
                ax.get_yticks,
                ax.yaxis.set_major_locator,
            )
        else:
            get_lim, set_lim, get_ticks, set_locator = (
                ax.get_xlim,
                ax.set_xlim,
                ax.get_xticks,
                ax.xaxis.set_major_locator,
            )

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


def enable_grid(ax):
    """
    Enable grid on the given Axes object with specific styling.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to enable the grid on.
    """
    ax.grid(True, alpha=0.8, linewidth=0.3)
    ax.set_axisbelow(True)  # Ensure grid is below the plot elements


def set_spines_linewidth(
    ax: plt.Axes,
    linewidth: float = 0.5,
) -> None:
    """
    Set the line width of all four spines (top, bottom, left, right) of the given Axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object whose spines will be modified.
    linewidth : float, optional
        The desired line width for the spines (default is 0.5).

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> set_spines_linewidth(ax, linewidth=0.8)
    """
    for spine in ax.spines.values():
        spine.set_linewidth(linewidth)


def set_ticks_inside(ax: plt.Axes, width: float = 0.5, x_pad: float = None) -> None:
    """
    Move all ticks inside the plot, set their line width, and optionally adjust padding for x-axis labels.


    Parameters
    ----------
    ax : matplotlib.axes.Axes
    The Axes object whose ticks will be modified.
    width : float, optional
    The desired width of the ticks (default is 0.5).
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
        'single' -> width 8.8 cm, 'double' -> width 18.2 cm. Default is 'single'.
    forward : bool, optional
        If True, also resizes the canvas in GUI backends (default is True).

    Notes
    -----
    - Height is automatically set using the golden ratio: height = width * 0.618.
    - Call plt.draw() after resizing if the figure is already displayed to update the canvas.

    Raises
    ------
    ValueError
        If layout is not 'single' or 'double'.

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> resize_figure(fig, layout='double')
    """
    gold_ratio = 0.618

    if layout == "single":
        width_cm = 8.8
    elif layout == "double":
        width_cm = 18.0
    else:
        raise ValueError("layout must be 'single' or 'double'")

    height_cm = width_cm * gold_ratio

    width_in = width_cm / 2.54
    height_in = height_cm / 2.54

    fig.set_size_inches(width_in, height_in, forward=forward)
    plt.draw()


def main(fig, ax, layout: str = "single") -> None:
    """
    # Example function to demonstrate usage of even_ticks and enable_grid.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to apply the functions on.
    layout : str, optional
        Either 'single' or 'double'. Determines the width of the figure.
        'single' -> width 8.8 cm, 'double' -> width 18.2 cm. Default is 'single'.
    """
    # Set spines line width
    set_spines_linewidth(ax)

    # Adjust ticks to be inside and match spine width
    set_ticks_inside(ax, x_pad=5)

    # Enable grid
    enable_grid(ax)

    # Adjust ticks
    even_ticks(ax)

    # Resize figure to golden ratio
    resize_figure(fig, layout)
