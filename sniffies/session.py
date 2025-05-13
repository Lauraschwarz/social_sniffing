import os
import pathlib
import warnings
from pathlib import Path
from shutil import copyfile

import looming_spots.loom_io.load
import numpy as np
from datetime import datetime

from cached_property import cached_property

import harp_python as hp
from sniffies import Sniff, Track, trial
PROCESSED_DATA_DIRECTORY = r"F:\social_sniffing\derivatives"
class Session(object):

    """
    The Session class aims to load data that has been acquired in a series of recording sessions and provide
    a simple means to read and access this data, trials are generated from this data and have access to the data
    provided.

    """

    def __init__(
        self,
        mouse_id,
        session_path,
        
    ):
        self.mouse_id = mouse_id
        self.n_trials_to_exclude = n_trials_to_exclude
        self.next_session = None
        self.previous_session = None
        self.session_path = session_path
        self.rawdata_path = session_path.replace("derivatives", "rawdata")
        self.dt = session_path.name

    def __len__(self):
        return len(self.data["photodiode"])

    def __lt__(self, other):
        """
        Allows sorting trials chronologically

        :param other:
        :return:
        """
        return self.dt < other.dt

    def __gt__(self, other):
        """
        Allows sorting trials chronologically

        :param other:
        :return:
        """
        return self.dt > other.dt

    def __add__(self, a):
        for t in self.trials:
            t + a

   

    @cached_property
    def trials(self):
        trials_idx = self.get_trial_onsets()

        trials = self.initialise_trials(
            trials_idx, 
            stimulus_type="conspecific"
        )

        return sorted(trials)
    
    @cached_property
    def get_trial_onsets(self):
        """
        Returns the trial onsets for the session. 
        The trial onsets are defined as the indices of where the light of the lickport turns on.

        when creating the reader object, it required the device.yaml to be in that directory, 
        if it isnt it will crash.
        :return:
        """
        output_set = hp.create_reader(directory=self.directory, epoch=hp.REFERENCE_EPOCH)
        read_path = [path for path in (session_dir.rglob("*34_*.bin") )]
        output_set = output_set.OutputSet.read(read_path
        )
        port0 = output_set["DIOport0"]
        trial_onsets = port0[port0 == True].index
        
        return trial_onsets


    def initialise_trials(self, idx, stimulus_type):
        if idx is not None:
            if len(idx) > 0:
                trials = []
                for i, onset in enumerate(idx):
                    t = trial.Trial(
                            self,
                            directory=self.session_path,
                            sample_number=onset,
                            stimulus_type="conspecific",
                        )
                    
                    trials.append(t)
                return trials
        else:
            return ValueError("No trials found")
   

    def get_trial_type(self, sample_number):
        """
        Returns the trial type of the trial at the given sample number.

        :param sample_number:
        :return:
        """
   

    def get_trials_of_protocol_type(self, key):
        """
        Returns trials grouped as either belonging to an LSE protocol, or being a testing trial of some sort
        to later be more specifically classified as a pre- or post- lse testing trial.

        :param key:
        :return:
        """
        if key == "conspecific":
            return [t for t in self.trials if "conspecific" in t.trial_type]

        return [t for t in self.trials if t.trial_type == key]

  
    @cached_property
    def looming_stimuli_idx(self):
        loom_idx_path = os.path.join(self.path, "loom_starts.npy")
        if not os.path.isfile(loom_idx_path):
            _ = photodiode.get_loom_idx_from_photodiode_trace(self.path, save=True)[0]


    def get_data(self, key):
        data_func_dict = {
            "x_pos": self.x_pos,
            "y_pos": self.y_pos,
            "trials": self.get_session_trials,
        }

        return data_func_dict[key]


    def track(self):
        return track_functions.track_in_standard_space(
            self.path, get_tracking_method(self.path), 0, len(self), None
        )

    def x_pos(self):
        return self.track()[0]

    def y_pos(self):
        return self.track()[1]

    @classmethod
    def set_next_session(cls, self, other):
        setattr(self, "next_session", other)

    @classmethod
    def set_previous_session(cls, self, other):
        setattr(self, "previous_session", other)


def load_sessions(mouse_id):
    mouse_directory = pathlib.Path(PROCCESSED_DATA_DIRECTORY / mouse_id)
    print(f"loading.... {mouse_directory}")
    session_list = []
    if os.path.isdir(mouse_directory):

        for s in os.listdir(mouse_directory):

            session_directory = os.path.join(mouse_directory, s)
            if not os.path.isdir(session_directory):
                continue

            file_names = os.listdir(session_directory)

            if not contains_analog_input(file_names):
                continue

        
            if not contains_video(file_names) and not contains_tracks(
                session_directory
                ):
                print("no video or tracks")
                if not get_tracks_from_raw(
                    mouse_directory.replace("derivatives", "rawdata")
                    ):
                    continue

            s = Session(mouse_id=mouse_id, session_path=session_directory)  
            session_list.append(s)

        if len(session_list) == 0:
            msg = f"the mouse: {mouse_id} has not been processed"
            raise MouseNotFoundError(msg)

        return sorted(session_list)
    msg = f"the mouse: {mouse_id} has not been copied to the processed data directory"
    warnings.warn(msg)

    raise MouseNotFoundError()


def contains_analog_input(file_names):
    if "AI.bin" in file_names or "AI.tdms" in file_names:
        return True
    return False


def contains_video(file_names):
    return any(".avi" in fname for fname in file_names) or any(
        ".mp4" in fname for fname in file_names
    )


def contains_tracks(session_directory):
    p = pathlib.Path(session_directory)
    if len(list(p.rglob("*.h5"))) == 0:
        return False
    else:
        return True


def get_tracks_from_raw(directory):
    print(f"getting tracks from {directory}")
    p = Path(directory)
    track_paths = p.rglob("*tracks.npy")
    if len(list(p.rglob("*tracks.npy"))) == 0:
        print("no track paths found...")
        return False

    for tp in track_paths:
        raw_path = str(tp)
        processed_path = raw_path.replace("rawdata", "derivatives")
        print(f"copying {raw_path} to {processed_path}")
        copyfile(raw_path, processed_path)
    return True