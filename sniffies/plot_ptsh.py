import numpy as np
from movement.io import load_poses
from edited_movement_func import plot_centroid_trajectory
from movement.roi import PolygonOfInterest
import movement as mvm
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
from global_functions import filter_positions, get_barrier_open_time

cmp = sns.diverging_palette(220, 20, as_cmap=True)


session = session.Session(
    mouse_id='1125131',
    session_path=r'F:\social_sniffing\derivatives\1125131\2025-07-01T12-47-28')
starts, ends = session.get_trial_onsets()
trial = session.trials
sniff = trial[0].sniffing.analogdataraw
photo = session.photometry
deltaF = photo.align_to_behav_time()
signal, background = photo.clip_photometry()
#video_start = trial[0].track.timestamps[0]
num_trials = len(trial)
stepmotor = get_barrier_open_time(session.rawdata_path)

deltaF_z = (deltaF - deltaF.mean()) / deltaF.std()

window_pre = 5  # seconds before onset
window_post = 5  # seconds after onset (adjust as needed)
frame_rate = 50  # or your actual frame rate

window_len = int((window_pre + window_post) * frame_rate)
time_axis = np.linspace(-window_pre, window_post, window_len)
ptsh_matrix = []
# Get time-of-day for all deltaF_z index entries
deltaF_times = np.array([ts.time() for ts in deltaF_z.index])
ptsh_matrix = []


def get_entry_onsets(isinside, min_duration=0):
    isinside = np.asarray(isinside)
    transitions = np.where((~isinside[:-1]) & (isinside[1:]))[0] + 1
    ends = np.where((isinside[:-1]) & (~isinside[1:]))[0] + 1

    if isinside[0]:
        transitions = np.insert(transitions, 0, 0)
    if isinside[-1]:
        ends = np.append(ends, len(isinside))

    valid_onsets = []
    for start, end in zip(transitions, ends):
        if (end - start) >= min_duration:
            valid_onsets.append(start)
    return np.array(valid_onsets)

def define_conspecific_approach(track):
    distance = mvm.kinematics.distances.compute_pairwise_distances(track.position, "individuals", "all", metric='euclidean')
    abdomen_distance = distance.sel(**{'1': 'abdomen', '2': 'abdomen'})
    is_close = abdomen_distance < 150
    is_close_onsets = get_entry_onsets(is_close, min_duration=15).astype(int)

    if len(is_close_onsets) == 0:
        return None
    else:
        return trial[0].track.video_timestamps[is_close_onsets]

def define_poke_onsets(sniff, track):
    poke0_events = sniff.get_pokes('DIPort0')
    poke1_events = sniff.get_pokes('DIPort1')


    if len(poke0_events) == 0 and len(poke1_events) == 0:
        return None
    else:
        return trial[0].track.video_timestamps[np.concatenate([poke0_events, poke1_events])]



def define_port_entry_onsets(track):
    port0 = PolygonOfInterest(ARENA['port0'], name='port0')
    port1 = PolygonOfInterest(ARENA['port1'], name='port1')
    isinside0 = port0.contains_point(track.position.sel(individuals='2', keypoints='abdomen'))
    isinside1 = port1.contains_point(track.position.sel(individuals='2', keypoints='abdomen'))
    
    port0_onsets = get_entry_onsets(isinside0).astype(int)
    port1_onsets = get_entry_onsets(isinside1).astype(int)

    merged_onsets = np.concatenate([port0_onsets, port1_onsets])
    merged_onsets = np.sort(merged_onsets)

    if len(merged_onsets) == 0:
        return None
    else:
        return trial[0].track.video_timestamps[merged_onsets]

def get_single_onset_signal(onset):
    window_start = onset - pd.Timedelta(seconds=window_pre)
    window_end = onset + pd.Timedelta(seconds=window_post)
    # Extract deltaF for this window
    window = deltaF_z.loc[window_start:window_end]
    return onset, window

def get_stim_onset_ptsh(ptsh_matrix, trial):

    for i, t in enumerate(trial):
        onset = t.start
        # Calculate window start and end
        window_start = onset - pd.Timedelta(seconds=window_pre)
        window_end = onset + pd.Timedelta(seconds=window_post)
        # Extract deltaF for this window
        window = deltaF_z.loc[window_start:window_end]
        # If window is too short (e.g., first trial), pad with NaN at the start
        if len(window) < window_len:
            pad_len = window_len - len(window)
            window = np.concatenate([np.full(pad_len, np.nan), window.values])
        else:
            window = window.values[:window_len]
        ptsh_matrix.append(window)
    ptsh_matrix = np.array(ptsh_matrix)
    return ptsh_matrix

def time_to_seconds(t):
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


def get_positional_onset_ptsh(ptsh_matrix, trial):

    track = trial[0].track.track_dataset
    track = filter_positions(track)
    onset_times = define_conspecific_approach(track)
    #onset_times = define_port_entry_onsets(track)
    for onset in onset_times:
        if not isinstance(onset, pd.Timestamp):
            onset = pd.to_datetime(onset, unit='s')
        window_start = (onset - pd.Timedelta(seconds=window_pre)).time()
        window_end = (onset + pd.Timedelta(seconds=window_post)).time()

        # Convert to seconds since midnight for matching
        deltaF_times_sec = np.array([time_to_seconds(tt) for tt in deltaF_times])
        start_sec = time_to_seconds(window_start)
        end_sec = time_to_seconds(window_end)

        # Find closest indices
        start_idx = np.argmin(np.abs(deltaF_times_sec - start_sec))
        end_idx = np.argmin(np.abs(deltaF_times_sec - end_sec))

        # Ensure correct order
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx

        window = deltaF_z.iloc[start_idx:end_idx+1].values

        # Pad if needed
        if len(window) < window_len:
            pad_len = window_len - len(window)
            window = np.concatenate([np.full(pad_len, np.nan), window])
        else:
            window = window[:window_len]
        ptsh_matrix.append(window)

    ptsh_matrix = np.array(ptsh_matrix)
    return ptsh_matrix

def plot_single_event(onset, signal, threshold=150):
    fig, ax = plt.subplots(figsize=(10, 5))
    track = trial[0].track.track_dataset
    video_timestamps = trial[0].track.video_timestamps
    distance = mvm.kinematics.distances.compute_pairwise_distances(track.position, "individuals", "all", metric='euclidean')
    snout_distance = distance.sel(**{'1': 'abdomen', '2': 'abdomen'})
    snout_distance = pd.Series(
    distance.sel(**{'1': 'abdomen', '2': 'abdomen'}).values,
    index=pd.to_datetime(video_timestamps, unit='s')
)
    
    correct_year = signal.index[0].year
    snout_distance.index = snout_distance.index.map(lambda ts: ts.replace(year=correct_year))
    snout_distance = snout_distance[~snout_distance.index.duplicated(keep='first')]
    nearest_idx = snout_distance.index.get_indexer([onset], method='nearest')
    window_start = nearest_idx - pd.Timedelta(seconds=window_pre)
    window_end = nearest_idx + pd.Timedelta(seconds=window_post)
    snout_distance = snout_distance.loc[window_start:window_end]
    

    below = snout_distance < threshold
    # Find contiguous regions where below is True
    in_region = False
    start = None
    for idx, val in enumerate(below):
        if val and not in_region:
            in_region = True
            start = snout_distance[idx]
        elif not val and in_region:
            in_region = False
            end = snout_distance[idx]
            ax.axvspan(start, end, color='lightgrey', alpha=0.5, zorder=0)
    # Handle case where region goes to end
    if in_region:
        ax.axvspan(start, snout_distance[-1], color='lightgrey', alpha=0.5, zorder=0)
    ax.plot(signal, color='k')
    ax.axhline(0, color='gray', linestyle='--')
    ax.axvline(x=onset, color='red', linestyle='--', label='Onset')
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("ΔF/F (z-scored)")
    ax.set_title("ΔF/ aligned to Barrier opening")
    plt.savefig(pathlib.Path(session.session_path) / 'plots' / 'barrier_opening.png')
    plt.show()

def plot_ptsh_matrix(ptsh_matrix):
    fig, (ax_mean, ax_heat) = plt.subplots(
        2, 1, figsize=(10, 8), 
        gridspec_kw={'height_ratios': [1, 3]}, 
        sharex=True
    )

    # Plot mean PSTH
    mean_psth = np.nanmean(ptsh_matrix, axis=0)
    ax_mean.plot(mean_psth, color='k')
    ax_mean.set_ylabel("Mean ΔF/F (z)")
    ax_mean.set_title("Mean PTSH")

    # Plot heatmap
    sns.heatmap(ptsh_matrix, cmap="vlag", center=0, ax=ax_heat, cbar_kws={'label': 'ΔF/F (z-scored)'})
    ax_heat.set_xlabel("Time (s)")
    ax_heat.set_ylabel("Trial")
    xticks = np.linspace(0, ptsh_matrix.shape[1]-1, 7)
    xticklabels = np.round(np.linspace(-window_pre, window_post, 7), 1)
    ax_heat.set_xticks(xticks)
    ax_heat.set_xticklabels(xticklabels)
    ax_heat.set_title("PTSH: Z-scored ΔF/F aligned to conspecific proximity")

    plt.tight_layout()
    plt.savefig(pathlib.Path(session.session_path) / 'plots' / 'ptsh_heatmap_conspecific_proximity.png')
    plt.show()

onset, signal = get_single_onset_signal(onset=pd.to_datetime(stepmotor, unit='s')[0])
plot_single_event(onset, signal)
#plot_ptsh_matrix(ptsh_matrix)