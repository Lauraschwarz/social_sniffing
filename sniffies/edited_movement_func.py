"""Wrappers to plot movement data."""

import xarray as xr
from matplotlib import pyplot as plt
import movement.kinematics as kin

DEFAULT_PLOTTING_ARGS = {
    "s": 15,
    "marker": "o",
    "alpha": 1.0,
}


def plot_centroid_trajectory(
        da: xr.DataArray,
        individual: str | None = None,
        keypoints: str | list[str] | None = None,
        ax: plt.Axes | None = None,
        manual_color_var=False,
        suppress_colorbar=False,
        **kwargs,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot centroid trajectory.

    This function plots the trajectory of the centroid
    of multiple keypoints for a given individual. By default, the trajectory
    is colored by time (using the default colormap). Pass a different colormap
    through ``cmap`` if desired. If a single keypoint is passed, the trajectory
    will be the same as the trajectory of the keypoint.

    Parameters
    ----------
    da : xr.DataArray
        A data array containing position information, with `time` and `space`
        as required dimensions. Optionally, it may have `individuals` and/or
        `keypoints` dimensions.
    individual : str, optional
        The name of the individual to be plotted. By default, the first
        individual is plotted.
    keypoints : str, list[str], optional
        The name of the keypoint to be plotted, or a list of keypoint names
        (their centroid will be plotted). By default, the centroid of all
        keypoints is plotted.
    ax : matplotlib.axes.Axes or None, optional
        Axes object on which to draw the trajectory. If None, a new
        figure and axes are created.
    **kwargs : dict
        Additional keyword arguments passed to
        ``matplotlib.axes.Axes.scatter()``.

    Returns
    -------
    (figure, axes) : tuple of (matplotlib.pyplot.Figure, matplotlib.axes.Axes)
        The figure and axes containing the trajectory plot.

    """
    if isinstance(individual, list):
        raise ValueError("Only one individual can be selected.")

    selection = {}

    if "individuals" in da.dims:
        if individual is None:
            selection["individuals"] = da.individuals.values[0]
        else:
            selection["individuals"] = individual

    if "keypoints" in da.dims:
        if keypoints is None:
            selection["keypoints"] = da.keypoints.values
        else:
            selection["keypoints"] = keypoints

    plot_point = da.sel(**selection)

    # If there are multiple selected keypoints, calculate the centroid
    plot_point = (
        plot_point.mean(dim="keypoints", skipna=True)
        if "keypoints" in plot_point.dims and plot_point.sizes["keypoints"] > 1
        else plot_point
    )

    plot_point = plot_point.squeeze()  # Only space and time should remain

    fig, ax = plt.subplots(figsize=(6, 6)) if ax is None else (ax.figure, ax)

    # Merge default plotting args with user-provided kwargs
    for key, value in DEFAULT_PLOTTING_ARGS.items():
        kwargs.setdefault(key, value)

    colorbar = True if not suppress_colorbar else False

    if "c" not in kwargs:
        if manual_color_var and (manual_color_var in plot_point.attrs):
            kwargs["c"] = plot_point.attrs[manual_color_var]
            time_label = manual_color_var
        else:
            kwargs["c"] = plot_point.time
            time_label = "Time"

    sc = ax.scatter(
        plot_point.sel(space="x"),
        plot_point.sel(space="y"),
        **kwargs,
    )

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Trajectory")

    time_label = manual_color_var if (manual_color_var and (manual_color_var in plot_point.attrs)) else "Time"
    fig.colorbar(sc, ax=ax, label=time_label).solids.set(
        alpha=1.0
    ) if colorbar else None

    return fig, ax


def selection(
        da: xr.DataArray,
        individual: str | None = None,
        keypoints: str | list[str] | None = None,
        **kwargs,

):
    if isinstance(individual, list):
        raise ValueError("Only one individual can be selected.")

    selection = {}

    if "individuals" in da.dims:
        if individual is None:
            selection["individuals"] = da.individuals.values[0]
        else:
            selection["individuals"] = individual

    if "keypoints" in da.dims:
        if keypoints is None:
            selection["keypoints"] = da.keypoints.values
        else:
            selection["keypoints"] = keypoints

    plot_point = da.sel(**selection)

    # If there are multiple selected keypoints, calculate the centroid
    plot_point = (
        plot_point.mean(dim="keypoints", skipna=True)
        if "keypoints" in plot_point.dims and plot_point.sizes["keypoints"] > 1
        else plot_point
    )

    plot_point = plot_point.squeeze()  # Only space and time should remain
    return plot_point


def plot_centroid_trajectory_quiver(
        da: xr.DataArray,
        individual: str | None = None,
        keypoints: str | list[str] | None = None,
        ax: plt.Axes | None = None,
        manual_color_var=False,
        suppress_colorbar=False,
        **kwargs,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot centroid trajectory.

    This function plots the trajectory of the centroid
    of multiple keypoints for a given individual. By default, the trajectory
    is colored by time (using the default colormap). Pass a different colormap
    through ``cmap`` if desired. If a single keypoint is passed, the trajectory
    will be the same as the trajectory of the keypoint.

    Parameters
    ----------
    da : xr.DataArray
        A data array containing position information, with `time` and `space`
        as required dimensions. Optionally, it may have `individuals` and/or
        `keypoints` dimensions.
    individual : str, optional
        The name of the individual to be plotted. By default, the first
        individual is plotted.
    keypoints : str, list[str], optional
        The name of the keypoint to be plotted, or a list of keypoint names
        (their centroid will be plotted). By default, the centroid of all
        keypoints is plotted.
    ax : matplotlib.axes.Axes or None, optional
        Axes object on which to draw the trajectory. If None, a new
        figure and axes are created.
    **kwargs : dict
        Additional keyword arguments passed to
        ``matplotlib.axes.Axes.scatter()``.

    Returns
    -------
    (figure, axes) : tuple of (matplotlib.pyplot.Figure, matplotlib.axes.Axes)
        The figure and axes containing the trajectory plot.

    """
    if isinstance(individual, list):
        raise ValueError("Only one individual can be selected.")

    selection = {}

    if "individuals" in da.dims:
        if individual is None:
            selection["individuals"] = da.individuals.values[0]
        else:
            selection["individuals"] = individual

    if "keypoints" in da.dims:
        if keypoints is None:
            selection["keypoints"] = da.keypoints.values
        else:
            selection["keypoints"] = keypoints

    plot_point = da.sel(**selection)

    plot_point = (
        plot_point.mean(dim="keypoints", skipna=True)
        if "keypoints" in plot_point.dims and plot_point.sizes["keypoints"] > 1
        else plot_point
    )

    plot_point = plot_point.squeeze()  # Only space and time should remain

    fig, ax = plt.subplots(figsize=(6, 6)) if ax is None else (ax.figure, ax)

    # Merge default plotting args with user-provided kwargs
    for key, value in DEFAULT_PLOTTING_ARGS.items():
        kwargs.setdefault(key, value)

    colorbar = True if not suppress_colorbar else False

    if "c" not in kwargs:
        if manual_color_var and (manual_color_var in plot_point.attrs):
            kwargs["c"] = plot_point.attrs[manual_color_var]
            time_label = manual_color_var
        else:
            kwargs["c"] = plot_point.time
            time_label = "Time"

    sc = ax.scatter(
        plot_point.sel(space="x"),
        plot_point.sel(space="y"),
        **kwargs,
    )

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Trajectory")

    time_label = manual_color_var if (manual_color_var and (manual_color_var in plot_point.attrs)) else "Time"
    fig.colorbar(sc, ax=ax, label=time_label).solids.set(
        alpha=1.0
    ) if colorbar else None

    return fig, ax