import movement as mvm
import numpy as np  
import pathlib 
import pandas as pd

class Track(object):

   def __init__(folder, 
        path,
        start,
        end, 
        frame_rate):
        """
        Initialize the Sniff object with the given parameters.  
        :param folder: The folder where the data is stored.
        :param data: x and y position stream from sleap file. positional data is read using movement
        """
       
        self.folder = folder
        self.path = pathlib.Path(path)
        self.start = start
        self.end = end
        self.frame_rate = frame_rate
        track_dataset = mvm.io.load_poses.from_sleap_file(self.path, frame_rate=self.frame_rate)
        self.track = track_dataset.position
        self.video_timestamps = pd.load_csv([path for path in (self.folder.rglob("*.csv") )], header=None)[0]
        self.frame_index = self.video_timestamps.index[start:end]


        def convert_timedouble_to_datetime(epoch, time_double):
            """
            Convert a time double to a datetime object.
            :param epoch: The epoch time (datetime object).
            :param time_double: The time double value.
            :return: The corresponding datetime object.
            """
            return epoch + pd.to_timedelta(time_double, unit='s')
        self.datetime = self.video_timestamps.apply(lambda x: epoch + timedelta(days=x))
   