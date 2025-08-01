import numpy as np
from movement.io import load_poses
from edited_movement_func import plot_centroid_trajectory
from movement.roi import PolygonOfInterest
from skimage import measure
import matplotlib
from ultra import get_exploration_and_signal_grid
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
import session 
import seaborn as sns 
import pathlib
from constants import ARENA
cmp = sns.diverging_palette(220, 20, as_cmap=True)


session = session.Session(
    mouse_id='1125132',
    session_path=r'F:\social_sniffing\derivatives\1125132\2025-07-02T14-37-53')
starts, ends = session.get_trial_onsets()
trial = session.trials
photo = session.photometry
deltaF = photo.align_to_behav_time()
signal, background = photo.clip_photometry()
#video_start = trial[0].track.timestamps[0]
num_trials = len(trial)


# def plot_delta_f_trace(ax, t, trace, frame_rate):
#     ax.plot(trace.index,  trace)
#     ax.scatter(trace.index, trace, c=trace.index, s=1, zorder=100, cmap=cmp)
#     ax.format(
#                 #ylim=[min(trace), max(trace)],
#                 #xlim=[t.start, t.end],
#                 ylabel='ΔF/F',
#                 xlabel='Time (s)'
#     )
def plot_delta_f_trace(ax, t, trace, frame_rate, distance=None, threshold=None):
    if distance is not None and threshold is not None:
        below = distance < threshold
        # Find contiguous regions where below is True
        in_region = False
        start = None
        for idx, val in enumerate(below):
            if val and not in_region:
                in_region = True
                start = trace.index[idx]
            elif not val and in_region:
                in_region = False
                end = trace.index[idx]
                ax.axvspan(start, end, color='lightgrey', alpha=0.5, zorder=0)
        # Handle case where region goes to end
        if in_region:
            ax.axvspan(start, trace.index[-1], color='lightgrey', alpha=0.5, zorder=0)

    ax.plot(trace.index, trace)
    ax.scatter(trace.index, trace, c=trace.index, s=1, zorder=100, cmap=cmp)
    ax.format(
        ylabel='ΔF/F',
        xlabel='Time (s)'
    )

def load_roi(name):
    roi = PolygonOfInterest(ARENA[name], name='name')
    return roi


batch_size = 4
num_trials = len(trial)

for batch_start in range(0, num_trials, batch_size):
    batch_end = min(batch_start + batch_size, num_trials)
    trial_batch = trial[batch_start:batch_end]

    # Create new figure and axes for each batch
    arena_fig, arena_axes = get_exploration_and_signal_grid(
        n_conditions=len(trial_batch),
        add_row=True,
        n_add_rows=1,
        figsize=(14, 11),
    )
    for i, t in enumerate(trial_batch):
        
        position_by_time_ax = arena_axes[i]
        position_by_deltaf_ax = arena_axes[i + len(trial_batch)] # not sure about indexing so maybe check this
        deltaf_trace_ax = arena_axes[i + (len(trial_batch) * 2)]
        start_time = pd.Timestamp(t.start).time()
        end_time = t.end.time()
        delta_f = deltaF.between_time(start_time, end_time)

        sniff = t.sniffing.extract_sniff_freq()
    
        
        track = t.track
        frame_datetimes = trial[0].start + pd.to_timedelta(track.ds.time, unit='s')
        #sniff_aligned = sniff.reindex(frame_datetimes, method='nearest')
        delta_f = delta_f.sort_index()
        delta_f.index = pd.to_datetime(delta_f.index)

        delta_f_aligned = pd.Series(index=frame_datetimes, dtype=float)
        delta_f_aligned[:] = delta_f.asof(frame_datetimes).values


        # Assign to your positional data
        track.ds = track.ds.assign_coords(delta_f=delta_f_aligned.values)
        distance = track.individual_distances()
        snout_distance = distance.sel(**{'1': 'abdomen', '2': 'abdomen'})
        # port0_distance, port1_distance = track.distance_to_port(track.ds.position)
        # port0_distance = port0_distance.sel(individuals='2', keypoints='abdomen')
        # port1_distance = port1_distance.sel(individuals='2', keypoints='abdomen')
        # distance_from_wall = track.isin_ROI(track.ds.position)
        # distance_from_wall = distance_from_wall.sel(individuals='2', keypoints='abdomen')
        abdomen_position = track.ds.position.sel(individuals='2', keypoints='abdomen')
        
        exp_positions = track.ds.position.sel(individuals='2')
        exp_positions.attrs["delta_f"] = delta_f_aligned

        # raw_sniff = t.sniffing.analog 
        # poke0 = t.sniffing.get_pokes('DIPort0')
        # poke1 = t.sniffing.get_pokes('DIPort1')
        # valve0 = t.sniffing.get_valve_open('SupplyPort0')
        # valve1 = t.sniffing.get_valve_open('SupplyPort1')

    #plot_sniff_deltaF(sniff_resampled, delta_f_resampled)
        ### if you have ROIS load them and plot them
        region_of_interest1 = load_roi('port0')
        
        roi2 = load_roi('port1')
        roi3 = load_roi('Arena')
        roi3.plot(position_by_time_ax, facecolor='lightgrey', linewidth=0, alpha=1)
        roi3.plot(position_by_deltaf_ax, facecolor='lightgrey', linewidth=0, alpha=1)
        roi2.plot(position_by_time_ax, facecolor='Grey', linewidth=0, alpha=1)
        roi2.plot(position_by_deltaf_ax, facecolor='Grey', linewidth=0, alpha=1)
        


        trace = delta_f_aligned
        plot_delta_f_trace(deltaf_trace_ax, t, trace, frame_rate=50, distance= snout_distance, threshold=200)

        suppress_colorbar = i not in [len(trial_batch) - 1,  # plot colorbar only for last plot (assuming cbar same for all columns)
                                    int(len(trial_batch) * 2) - 1]
        plot_centroid_trajectory(
            exp_positions,
            keypoints='abdomen',
            manual_color_var="delta_f",
            ax=position_by_deltaf_ax,
            linestyle="-",
            marker=".",
            s=3,
            vmax=0.1,
            vmin=-0.1,
            cmap=cmp,
            suppress_colorbar=suppress_colorbar,
        )
        plot_centroid_trajectory(
            exp_positions,
            keypoints='abdomen',
            ax=position_by_time_ax,
            linestyle="-",
            marker=".",
            s=3,
            cmap=cmp,
            suppress_colorbar=suppress_colorbar,
        )
    plt.title(f"Batch {batch_start} to {batch_end - 1} - Trials {batch_start + 1} to {batch_end}")
    plt.savefig(pathlib.Path(session.session_path) / 'plots' / f"trial_batch_{batch_start}_{batch_end}_10secs.png", dpi=300)
    plt.tight_layout()
