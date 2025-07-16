import os
import pathlib
import warnings
from pathlib import Path
from shutil import copyfile

import numpy as np
from datetime import datetime

from cached_property import cached_property

import harp as hp
import Sniff
import trial
import Track
import photometry
from global_functions import get_harp_paths, join_binary_files


PROCESSED_DATA_DIRECTORY = r"F:\social_sniffing\derivatives"
from constants import ARENA
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
        self.next_session = None
        self.previous_session = None
        self.session_path = session_path
        self.rawdata_path = session_path.replace("derivatives", "rawdata")
        self.path = pathlib.Path(session_path)
        self.trials = self.trials()

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

   

    
    def trials(self):
        trial_onsets_path = pathlib.Path(self.session_path) / "trial_onsets.npy"
        trial_ends_path = pathlib.Path(self.session_path) / "trial_ends.npy"

        if trial_onsets_path.exists() and trial_ends_path.exists():
            # Load from file if both exist
            trial_onsets = np.load(trial_onsets_path, allow_pickle=True)
            trial_ends = np.load(trial_ends_path, allow_pickle=True)
            
        else:
            # Otherwise, generate them
            trial_onsets, trial_ends = self.get_trial_onsets()        

        trials = self.initialise_trials(
            onsets=trial_onsets,
            trial_ends=trial_ends,
            stimulus_type="conspecific"
        )

        return trials
    
    
    def get_trial_onsets(self):
        """
        Returns the trial onsets for the session. 
        The trial onsets are defined as the indices of where the light of the lickport turns on.

        when creating the reader object, it required the device.yaml to be in that directory, 
        if it isnt it will crash.
        :return:
        """
        reader = hp.create_reader(r'F:/social_sniffing', epoch=hp.REFERENCE_EPOCH)

        output_set = reader.OutputSet.read(get_harp_paths(pathlib.Path(self.rawdata_path) / 'behav', register='34'))
        port0 = output_set["DOPort0"]
        trial_onsets = (port0[port0 == True].index)
        analog = reader.AnalogData.read(get_harp_paths(pathlib.Path(self.rawdata_path) / 'behav', register='44'))
        analog_timestamps = (analog['AnalogInput0'].index)
        end = []
        for i, onset in enumerate(analog_timestamps):
            start = onset
            if i < len(trial_onsets) - 1:
                next_start = trial_onsets[i + 1]
                idx = np.argmin(np.abs(analog_timestamps - next_start))
                nearest_timestamp = analog_timestamps[idx]
                end.append(nearest_timestamp)
        else:
            end.append(analog_timestamps[-1])
        #save to .npy
        trial_onsets = np.array(trial_onsets)
        end = np.array(end)
        save_dir = pathlib.Path(self.session_path)
        save_dir.mkdir(parents=True, exist_ok=True)

        np.save(pathlib.Path(save_dir, "trial_onsets.npy"), trial_onsets)
        np.save(pathlib.Path(save_dir, "trial_ends.npy"), end)
        return trial_onsets, end



    def initialise_trials(self, onsets, trial_ends, stimulus_type="conspecific"):
        if onsets is not None:
            if len(onsets) > 0:
                trials = []
                for i, onset in enumerate(onsets):
                    t = trial.Trial(
                            self,
                            session_path=self.session_path,
                            onset=onset,
                            trial_end=trial_ends[i],
                            stimulus_type="conspecific",
                        )
                    
                    trials.append(t)
                # Set next_trial and previous_trial links
                for i in range(len(trials) - 1):
                    trial.Trial.set_next_trial(trials[i], trials[i + 1])
                    trial.Trial.set_previous_trial(trials[i + 1], trials[i])
                return trials
        else:
            return ValueError("No trials found")
   
    def photometry(self):
        """
        Returns the photometry data for the session.
        :return: A DataFrame with the photometry data.
        """
        path = self.rawdata_path / "photo"


    

    def x_pos(self):
        return self.track()[0]

    def y_pos(self):
        return self.track()[1]
    
    @property
    def photometry(self):
        return photometry.photo(session_directory=self.rawdata_path, mouseID=self.mouse_id,
        frame_rate=50)

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


