import os
import pathlib

import numpy as np
import matplotlib.pyplot as plt
import pims

from constants import ARENA, TRIAL_LENGTH
from matplotlib import patches
from datetime import timedelta
import Sniff
import Track
import harp as hp

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
        session_path,
        onset,
        trial_end, 
        stimulus_type,
      
    ):
        self.session = session
        self.frame_rate = 50
        self.onset = onset
        self.mouse_id = self.session.mouse_id
        self.stimulus_type = stimulus_type
        self.directory = session_path
      
        self.video_path = pathlib.Path(f"{self.directory} / Video")
        self.folder = pathlib.Path(f"{self.directory}/ output_inference")
        self.rawdata_path = session_path.replace("derivatives", "rawdata")
        self.time_to_first_reward = None


        self.next_trial = None
        self.previous_trial = None

        self.start = onset
        fpaths = pathlib.Path(self.rawdata_path)
        
        self.end = trial_end
        #  so check if it is a datetime object and convert it to a sample number

 
    # def __gt__(self, other):
    #     return self.time > other.time

    # def __eq__(self, other):
    #     return self.time == other.time

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
        return Track.Track(
            self.directory,
            self.start,
            self.end,
            self.frame_rate,
        )
    @property
    def sniffing(self):
        return Sniff.harp_data(session_directory=self.directory, mouseID=self.mouse_id,
        start=self.start, end=self.end, frame_rate=self.frame_rate) 
   
   

    
    # @property
    # def time(self):
    #     return self.session.dt + timedelta(0, int(self.sample_number / self.frame_rate))

    # def plot_stimulus(self):
    #     ax = plt.gca()
    #     if self.stimulus_type == "auditory":
    #         plotting.plot_auditory_stimulus(self.n_samples_before)
    #     else:
    #         plotting.plot_looms_ax(ax)

    # def to_df(self, group_id, extra_data=None):
    #     n_points = TRACK_LENGTH
    #     track = pad_track(
    #         ARENA_SIZE_CM * self.track.normalised_x_track[0:n_points], n_points
    #     )
    #     unsmoothed_speed = pad_track(
    #         FRAME_RATE * ARENA_SIZE_CM * self.track.normalised_x_speed[0:n_points],
    #         n_points,
    #     )
    #     smoothed_speed = pad_track(
    #         FRAME_RATE * ARENA_SIZE_CM * self.track.smoothed_x_speed[0:n_points],
    #         n_points,
    #     )
    #     add_dict = {
    #         "group_id": group_id,
    #         "mouse_id": self.mouse_id,
    #         "track": [track],
    #         "speed": [smoothed_speed],
    #         "peak_speed": self.track.peak_speed(),
    #         "is_flee": self.track.is_escape(),
    #         "latency": self.track.latency(),
    #         "last_loom": get_most_recent_loom(self.track.latency()),
    #         "is_freeze": is_track_a_freeze(unsmoothed_speed),
    #         "time_to_shelter": self.track.time_to_shelter(),
    #     }

    #     if extra_data is not None:
    #         for k, v in extra_data.items():
    #             add_dict.setdefault(k, v)

    #     this_trial_df = pd.DataFrame.from_dict(add_dict)
    #     return this_trial_df


