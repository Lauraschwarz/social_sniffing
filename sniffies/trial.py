import os
import pathlib

import numpy as np
import matplotlib.pyplot as plt
import pims
from looming_spots.analyse.escape_classification import is_track_a_freeze
from looming_spots.analyse.track_functions import get_most_recent_loom
from looming_spots.db.track import Track
from looming_spots.util.generic_functions import pad_track

from matplotlib import patches
from datetime import timedelta
from sniffies import Sniff
from looming_spots.constants import (
    LOOMING_STIMULUS_ONSET,
    N_LOOMS_PER_STIMULUS,
    N_SAMPLES_BEFORE,
    ARENA_LENGTH_PX,
    ARENA_WIDTH_PX,
    ARENA_SIZE_CM,
    FRAME_RATE,
    TRACK_LENGTH,
)

from looming_spots.util import plotting
import pandas as pd


class Trial(object):

    """
    Trial associates trial-level metadata and data into one place.
    A trial is defined as a data window surrounding the presentation of a stimulus, as detected using a photodiode
    pulse presented in conjunction with a stimulus.


    This includes:

    - where the data comes from (i.e. the session, see session_io)
    - stimulus metadata (e.g. contrast, time, type)
    - trial data (e.g. the positional xy tracks (see db.track), photodiode traces and other coaquired data)

    """

    def __init__(
        self,
        session,
        directory,
        sample_number,
        stimulus_type,
      
    ):
        self.session = session
        self.frame_rate = self.session.frame_rate
        self.onset = sample_number
        self.mouse_id = self.session.mouse_id
        self.stimulus_type = stimulus_type
        self.directory = directory
      
        self.video_path = pathlib.Path(self.directory / "Video")
        self.folder = pathlib.Path(self.directory / "output_inference")

        self.time_to_first_reward = None


        self.trial_type = trial_type
        self.next_trial = None
        self.previous_trial = None

        self.start = self.sample_number
        self.end = self.next_trial.sample_number if self.next_trial is not None else max(self.sniffing.analogdata.index) #double chech this so it works
        

 
    def __gt__(self, other):
        return self.time > other.time

    def __eq__(self, other):
        return self.time == other.time

    def __add__(self, a):
        if not isinstance(a, int):
            raise TypeError
        self.sample_number += a
        self.start += a
        self.end += a

    @classmethod
    def set_next_trial(cls, self, other):
        setattr(self, "next_trial", other)

    @classmethod
    def set_previous_trial(cls, self, other):
        setattr(self, "previous_trial", other)

    
    @property
    def track(self):
        return Track(
            self.folder,
            self.session.path,
            self.start,
            self.end,
            self.frame_rate,
        )
    
    @property
    def sniffing(self):
        return Sniff(self.folder, 
        self.session.path,
        self.start,
        self.end, self.frame_rate)


    @property
    def loom_number(self):
        if self.sample_number in self.session.looming_stimuli_idx:
            return int(
                np.where(self.session.looming_stimuli_idx == self.sample_number)[0][0]
                / N_LOOMS_PER_STIMULUS
            )

    @property
    def auditory_number(self):
        if self.sample_number in self.session.auditory_stimuli_idx:
            return int(
                np.where(self.session.auditory_stimuli_idx == self.sample_number)[0][0]
            )

    def get_stimulus_number(self):
        return self.stimulus_number()

    @property
    def time(self):
        return self.session.dt + timedelta(0, int(self.sample_number / self.frame_rate))

    def plot_stimulus(self):
        ax = plt.gca()
        if self.stimulus_type == "auditory":
            plotting.plot_auditory_stimulus(self.n_samples_before)
        else:
            plotting.plot_looms_ax(ax)

    def to_df(self, group_id, extra_data=None):
        n_points = TRACK_LENGTH
        track = pad_track(
            ARENA_SIZE_CM * self.track.normalised_x_track[0:n_points], n_points
        )
        unsmoothed_speed = pad_track(
            FRAME_RATE * ARENA_SIZE_CM * self.track.normalised_x_speed[0:n_points],
            n_points,
        )
        smoothed_speed = pad_track(
            FRAME_RATE * ARENA_SIZE_CM * self.track.smoothed_x_speed[0:n_points],
            n_points,
        )
        add_dict = {
            "group_id": group_id,
            "mouse_id": self.mouse_id,
            "track": [track],
            "speed": [smoothed_speed],
            "peak_speed": self.track.peak_speed(),
            "is_flee": self.track.is_escape(),
            "latency": self.track.latency(),
            "last_loom": get_most_recent_loom(self.track.latency()),
            "is_freeze": is_track_a_freeze(unsmoothed_speed),
            "time_to_shelter": self.track.time_to_shelter(),
        }

        if extra_data is not None:
            for k, v in extra_data.items():
                add_dict.setdefault(k, v)

        this_trial_df = pd.DataFrame.from_dict(add_dict)
        return this_trial_df


class VisualStimulusTrial(LoomTrial):
    def __init__(
        self,
        session,
        directory,
        sample_number,
        trial_type,
        stimulus_type="loom",
    ):
        super().__init__(
            session,
            directory,
            sample_number,
            trial_type,
            stimulus_type,
            trial_video_fname="{}{}.mp4",
        )


class AuditoryStimulusTrial(LoomTrial):
    def __init__(
        self,
        session,
        directory,
        sample_number,
        trial_type,
        stimulus_type="auditory",
    ):
        super().__init__(session, directory, sample_number, trial_type, stimulus_type)

