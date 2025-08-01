import numpy as np
import pandas as pd
import harp as hp
import constants
import pathlib
from scipy.signal import find_peaks, savgol_filter, butter, sosfilt, sosfiltfilt
import matplotlib.pyplot as plt


class harp_data(object):
      """
      Initialize the Sniff object with the given parameters.  
      :param folder: The folder where the data is stored.
      :param data: Analog data stream from Harp behaviour box. harp-python reader required
      outputset: send command for activating lickports. DIOport0 and DIOport1 are the portlights (Set means turn on lights). 
               SupplyPOrt0 and SupplyPort1 the valves/ rewarddelivery
      outputclear: send command to clear the command (switch off lights and/or valves). 
      digitalinputstate: digital input state of the lickports. (detection of when the mouse pokes its head in the port)
      """
      def __init__(
         self,
         session_directory, 
         mouseID,
         start,
         end, 
         frame_rate, 
         module='behav'):
      
         self.session_path = session_directory
         self.module = module
         self.start = start
         self.end = end
         self.frame_rate = frame_rate
         self.mouseID = mouseID
         self.rawdata_path = self.session_path.replace("derivatives", "rawdata")
         reader = hp.create_reader(constants.DEVICE, epoch=hp.REFERENCE_EPOCH)


         self.analogdataraw = reader.AnalogData.read(self.get_harp_paths('44'))
         self.Outputset = reader.OutputSet.read(self.get_harp_paths('34'))
         self.Outputclear = reader.OutputClear.read(self.get_harp_paths('35'))
         self.digitalinputstate = reader.DigitalInputState.read(self.get_harp_paths('32'))
         self.frameacquired = reader.Camera0Frame.read(self.get_harp_paths('92'))

         self.Outputset = self.Outputset.between_time(pd.to_datetime(start).time(), end.time())
         self.Outputclear = self.Outputclear.between_time(pd.to_datetime(start).time(), end.time())
         self.digitalinputstate = self.digitalinputstate.between_time(pd.to_datetime(start).time(), end.time())
         self.frameacquired = self.frameacquired.between_time(pd.to_datetime(start).time(), end.time())
         self.analog = self.analogdataraw.between_time(pd.to_datetime(start).time(), end.time())
         self.analog = self.analog['AnalogInput0']
         
      
      def get_harp_paths(self, register):
            fpaths = pathlib.Path(self.rawdata_path) / "behav"
            read_path = [path for path in (fpaths.rglob(f"*_{register}_*.bin") )]
            if len(read_path) == 2:
               joined_path = self.join_binary_files(read_path[0], read_path[1])
               return joined_path
            elif len(read_path) > 2:
               # Look for a joined file
               joined_files = [p for p in fpaths.rglob(f"*_{register}*_joined.bin")]
               if joined_files:
                     return joined_files[0]
            elif len(read_path) == 1:
               return read_path[0]
            elif len(read_path) is None:
               raise FileNotFoundError(f"No harp data found for register {register} in {self.rawdata_path}.")
      
      def join_binary_files(self, fpath1, fpath2):
            out_path = fpath1.parent / f"{fpath1.stem}_joined.bin"
            if out_path.exists():
               print(f"Output file {out_path} already exists. Skipping join operation.")
               return out_path
            else:
               with open(out_path, 'wb') as outfile:
                  for f in [fpath1, fpath2]:
                     with open(f, 'rb') as infile:
                        outfile.write(infile.read())
                     return out_path

      def get_pokes(self, portname):
         """
         Get the pokes from the lickport.
         :param portname: The name of the port (e.g. 'DOPort0' or 'DOPort1').
         :return: A DataFrame with the timestamps of the pokes.
         """
         port = self.digitalinputstate[portname]
         pokes = port[port == True].index
         return pokes
      def get_valve_open(self, valve):
         """
         Get the timestamps when the valve is open.
         :param valve: The name of the valve (e.g. 'SupplyPort0' or 'SupplyPort1').
         """
         valve = self.Outputset[valve]
         valve_open = valve[valve == True].index
         return valve_open

      def smearlab_sniffing(self):
         window_length = int(0.05 * 9600)
         savgol_data = savgol_filter(self.analog, window_length=window_length, polyorder=3)
         smoothed_data = self.analog - savgol_data
         #zscored_data = (smoothed_data - smoothed_data.mean()) / smoothed_data.std()
         locs, properties = find_peaks(smoothed_data, height=(None, None), prominence=1, distance=15)
         peak_times = self.analog.index[locs]

         return smoothed_data, peak_times, properties
      

      def remove_trend_bandpass(data: np.array, lowcut: float = 0.1, highcut: float = 20, order: int = 5, f = 1000) -> np.array:

         sos_high = butter(order, lowcut, btype='highpass', output = 'sos', fs = f)
         highpassed = sosfiltfilt(sos_high, data)

         sos_low = butter(order, highcut, btype='lowpass', output = 'sos', fs = f)
         lowpassed = sosfiltfilt(sos_low, data)

         bandpassed = sosfiltfilt(sos_high, lowpassed)

         return bandpassed, lowpassed, highpassed
      
      

      def extract_sniff_freq(self, sampling_rate=9600, ewm_span=25, min_peak_distance_ms=5, prominence=1):
     
         trend = pd.Series(self.analog, index=self.analog.index).rolling(window=2400, center=True, min_periods=1).mean()
         detrended = pd.Series(self.analog, index=self.analog.index) - trend

         forward_ewm = detrended.ewm(span=ewm_span).mean()
         backward_ewm = detrended[::-1].ewm(span=ewm_span).mean()[::-1]
         smoothed = (forward_ewm + backward_ewm) / 2
         smoothed.index = self.analog.index  # Ensure index is preserved

         min_peak_distance = int((min_peak_distance_ms / 1000) * sampling_rate)
         peaks, _ = find_peaks(smoothed.values, prominence=prominence, distance=min_peak_distance)
         peak_times = self.analog.index[peaks]
 

         peak_intervals = np.diff(peak_times) / np.timedelta64(1, 's')
         peak_frequencies = 1 / peak_intervals
         freq_times = peak_times[1:]

         freq_series = pd.Series(peak_frequencies, index=freq_times)
         smoothed_freq = freq_series.ewm(span=5).mean()


         return smoothed_freq
      
      
      
      def stimulus_off(self, portname):
            return self.Outputclear[str(portname)].between_time(self.start, self.end)
      

      def filter_reward_window(self, start, portname):
         valve = self.get_valve_open(portname)
         valve_open = valve[valve == True].index
         if len(valve_open) == 0:
               stim_off = self.stimulus_off(portname)
               stim_off = stim_off[stim_off == True].index
               return stim_off
         else:
            return start, valve_open
               
          