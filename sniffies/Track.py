import movement as mvm
import numpy as np  
import pathlib 
import pandas as pd
from cached_property import cached_property
import xarray as xr
from datetime import timedelta, datetime 
from movement.filtering import filter_by_confidence, interpolate_over_time, savgol_filter
from movement.io import load_poses
from movement.roi import PolygonOfInterest
from movement.kinematics import distances
from constants import ARENA, ARENA_VERTICES, inner_vertices
class Track(object):
    """
        Initialize the Sniff object with the given parameters.  
        :param folder: The folder where the data is stored.
        :param data: x and y position stream from sleap file. positional data is read using movement
        """
    def __init__(
        self, 
        folder, 
        start,
        end, 
        frame_rate):
        self.folder = folder
        self.video_timestamps = pd.read_csv(([path for path
                                              in (pathlib.Path(self.folder.replace("derivatives", "rawdata")).rglob("*timestamps.csv") )][0]),
                                                header=None)[0]
        self.timestamps = self.convert_video_timestamps_to_datetime(self.video_timestamps)
        self.start = start
        self.end = end
        self.start_idx = self.datetime_to_frame_index(start)
        self.end_idx = self.datetime_to_frame_index(end)
        self.frame_rate = frame_rate
       
        self.track_dataset = mvm.io.load_poses.from_sleap_file(([path for path 
                                                            in (pathlib.Path(self.folder).rglob("*.h5") )][0]),
                                                              fps=self.frame_rate)
        
        self.ds: xr.DataArray = self.track_dataset.isel(time=slice(self.start_idx, self.end_idx))

        self.ds: xr.DataArray = self.filter_positions()




    def filter_positions(self, confidence_threshold=0.39):
        self.ds.update({
                "position": filter_by_confidence(
                self.ds.position, self.ds.confidence, threshold=confidence_threshold,print_report=True)})
        self.ds.update({
                "position": interpolate_over_time(self.ds.position, max_gap=50, print_report=True)})
        self.ds.update(
                {"position": savgol_filter(self.ds.position, 12)}
)
        return self.ds
    
    def convert_video_timestamps_to_datetime(self, video_timestamps):
        """
        Convert the video timestamps to datetime objects.
        :return: A pandas Series with the datetime objects.
        """
        mac_epoch = pd.Timestamp('1904-01-01 00:00:00')
        converted_series = video_timestamps.apply(lambda x: mac_epoch + pd.to_timedelta(x, unit='s'))
        return converted_series
    
    def datetime_to_frame_index(self, datetime_stamp):
       
        # Ensure both are pandas Timestamps for accurate comparison
        dt = pd.to_datetime(datetime_stamp)
        
        nearest_idx = np.argmin(np.abs(self.timestamps - dt))
        return nearest_idx


    def distance_to_port(self, positions):
        """
        Calculate the distance to the reward ports for each mouse. 
        :param track: The x and y coordinates of the mouse.
        :return: A np.array with the distances to the reward ports.ranging from 0 to 1.
        """
        port0 = PolygonOfInterest(ARENA['port0'], name='port0')
        port1 = PolygonOfInterest(ARENA['port1'], name='port1')

        distance_port0 = port0.compute_distance_to(positions)
        distance_port1 = port1.compute_distance_to(positions)

        return distance_port0, distance_port1
    
    def get_distance_from_wall(self, positions):
        """
        Check if the mouse is in the reward ports ROI. 
        :param track: The x and y coordinates of the mouse.
        :return: a boolean array with True if the mouse is in the ROI and False if not.
        """
        ring = PolygonOfInterest(ARENA_VERTICES, holes=[inner_vertices], name='ring')
        distance_from_wall = ring.compute_distance_to(positions)
        return distance_from_wall

    def individual_distances(self):
        """
        Calculate the distance between individuals in the arena.
        """
        distance = distances.compute_pairwise_distances(self.ds.position, "individuals", "all", metric='euclidean')
        return distance
    
    def position_in_roi(self, positions):
        """
        Check if the mouse is in the reward ports ROI. 
        :param track: The x and y coordinates of the mouse.
        :return: a boolean array with True if the mouse is in the ROI and False if not.
        """
        port0 = PolygonOfInterest(ARENA['port0'], name='port0')
        port1 = PolygonOfInterest(ARENA['port1'], name='port1')

        in_port0 = port0.contains_point(positions)
        in_port1 = port1.contains_point(positions)
        return in_port0, in_port1    

    @cached_property
    def get_first_track_in_roi(positions, roi_name):
        """
        Determine the first track that enters a specific ROI.
        :param tracks: List of Track objects.
        :param roi_name: The name of the ROI to check (e.g., 'port0' or 'port1').
        :return: The identity of the first track that enters the ROI, or None if no track enters.
        """
        roi = PolygonOfInterest(ARENA[roi_name], name=roi_name)

        first_track = None
        earliest_entry_time = None

        # Iterate through tracks
        for individual in positions.individuals.values:
            in_roi = roi.contains_point(positions)

            if in_roi.any():
                first_entry_index = np.argmax(in_roi)  
                entry_time = extract_timestamp_from_frame_index(first_entry_index)  #this wont work DEBUG

                if earliest_entry_time is None or entry_time < earliest_entry_time:
                    earliest_entry_time = entry_time
                    first_track = individual

        return first_track  

    def track_collected_reward(self, positions, roi_name):
        """
        extract the track which is most likey to have collected the reward. 
        it takes the first track that enters the ROI you determine when the rewad is collected
        :param positions: The x and y coordinates of the mouse.
        :param roi_name: The name of the ROI to check (e.g., 'port0' or 'port1'). """    
        start, valve_open = harp_data.filter_reward_window(self.start, roi_name)
        start = frame_index(start)
        valve_open_frame = frame_index(valve_open)
        track_ds = self.positions.sel(time=slice(start, valve_open_frame))
        winner = self.get_first_track_in_roi(track_ds, roi_name)
        return winner
    

    def frame_index(self, datetime_stamp):
        """
        Extract the frame index from the datetime stamps.
        :param datetime_stamps: The datetime stamps.
        :return: The corresponding frame index.
        """
        return self.video_timestamps.index[datetime_stamp]

 
        
    def extract_timestamp_from_frame_index(self, frame_index):
        """
        Extract the timestamp from the frame index.
        :param frame_index: The index of the frame.
        :return: The corresponding timestamp.
        """
        return self.video_timestamps.iloc[frame_index]

    
    