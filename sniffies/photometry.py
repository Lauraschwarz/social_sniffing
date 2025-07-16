import numpy as np
import pandas as pd
import harp as hp
import constants
import pathlib
from scipy.signal import find_peaks, savgol_filter, butter, sosfilt, sosfiltfilt, filtfilt
import matplotlib.pyplot as plt
from sklearn import linear_model

class photo(object):

    def __init__(
        self,
        session_directory, 
        mouseID,
        frame_rate, 
        module='photo'):

        self.session_path = session_directory
        self.module = module        
        self.rawdata_path = self.session_path.replace("derivatives", "rawdata")
        self.mouseID = mouseID
     

        self.harp_trigger_on = self.get_photometry_trigger_on()
        self.harp_trigger_off = self.get_photometry_trigger_off()
        self.behav_start_time, self.behav_end_time = self.get_behav_start_end()
        self.DIO_channel = self.get_photo_data()


    def get_photometry_trigger_on(self):
        reader = hp.create_reader(constants.OUTPUT_EXPANDER, epoch=hp.REFERENCE_EPOCH)
        fpath = pathlib.Path(self.rawdata_path) / 'OutputExpander'
        read_path = get_harp_paths(fpath, '35')
        if not read_path:
            raise FileNotFoundError("Outputexpander file not found.")
        output_expander_set = reader.OutputSet.read(read_path)
        return output_expander_set['Out0']
    
    def get_photometry_trigger_off(self):
        reader = hp.create_reader(constants.OUTPUT_EXPANDER, epoch=hp.REFERENCE_EPOCH)
        fpath = pathlib.Path(self.rawdata_path) / 'OutputExpander'
        read_path = get_harp_paths(fpath, '36')
        if not read_path:
            raise FileNotFoundError("Outputexpander file not found.")
        output_expander_clear = reader.OutputClear.read(read_path)
        return output_expander_clear['Out0']
    
    def get_photo_data(self, mode='DIO'):
          fpath = pathlib.Path(self.rawdata_path) / 'photo'
          file = list(fpath.rglob(f"*{mode}_*.csv"))
          if not file:
              raise FileNotFoundError(f"{mode} photometry file not found.")
          return pd.read_csv(file[0])
    
    def get_behav_start_end(self):
        reader = hp.create_reader(constants.DEVICE, epoch=hp.REFERENCE_EPOCH)
        read_path = get_harp_paths(self.rawdata_path, '44')
        if not read_path:
            raise FileNotFoundError("Analog data file not found.")
        analog_data = reader.AnalogData.read(read_path)
        analog_input = analog_data['AnalogInput0']
        return analog_input.index[0], analog_input.index[-1]
    
    def start_end_photo(self):
      
        dio_signal = self.DIO_channel['DIO01'].values
        dio_time = self.DIO_channel['Time'].values
        first_trigger_idx = np.where((dio_signal[:-1] == 0) & (dio_signal[1:] == 1))[0][0] + 1
        dio_first_trigger_time = dio_time[first_trigger_idx]
        falling_edges = np.where((dio_signal[:-1] == 1) & (dio_signal[1:] == 0))[0] + 1

        
        last_trigger_end_idx = falling_edges[-1]


        offset_from_start = self.harp_trigger_on.index[0] - self.behav_start_time
        true_start = dio_first_trigger_time - offset_from_start.total_seconds()
        dio_idx_start = np.where(dio_time >= true_start)[0][0]

        offset_to_end = self.behav_end_time - self.harp_trigger_off.index[-1] 
        dio_end_time = dio_time[last_trigger_end_idx] + offset_to_end.total_seconds()  
        dio_end_idx = np.where(dio_time <= dio_end_time)[0][-1] 

        return dio_idx_start, true_start, dio_end_idx, dio_end_time
    
    def clip_photometry(self):
        _, true_start, _, dio_end_time = self.start_end_photo()
        iso_signal = self.get_photo_data('AI0')
        calcium_signal = self.get_photo_data('AI1')
        closest_idx_start = (calcium_signal['Time'] - true_start).abs().idxmin()
        closest_row = calcium_signal.loc[closest_idx_start]
        closest_idx_end = (calcium_signal['Time'] - dio_end_time).abs().idxmin()
        closest_row_end = calcium_signal.loc[closest_idx_end]
        clipped_iso_signal = iso_signal[closest_idx_start:closest_idx_end]
        clipped_calcium_signal = calcium_signal[closest_idx_start:closest_idx_end]

        return  clipped_calcium_signal, clipped_iso_signal


    def get_delta_f(self):
        signal, background = self.clip_photometry()
        #signal_fit = apply_butterworth_lowpass_filter(signal['AIN01'], low_cut_off=15, fs=12166, order=4)
        #background_fit = apply_butterworth_lowpass_filter(background['AIN01'], low_cut_off=15, fs=12166, order=4)

        regression_params = np.polyfit(background['AIN01'], signal['AIN01'], 1)
        bg_fit = regression_params[0] * background['AIN01'] + regression_params[1]
        
        delta_f = (signal['AIN01'] - bg_fit) / bg_fit

        return delta_f
    
    def align_to_behav_time(self):
        signal, background = self.clip_photometry()
        signal['Time'] = signal['Time'] - signal['Time'].iloc[0]
        signal['timestamp'] = self.behav_start_time + pd.to_timedelta(signal['Time'], unit='s')
        delta_f = self.get_delta_f()
        signal['delta_f'] = delta_f
        signal = signal.set_index('timestamp')
        return signal['delta_f']
    
         
        

    def get_delta_f_using_robust_fit(self):
        background, signal = self.clip_photometry()

        signal_fit = signal['AIN01'][:-1] - robust_fit(signal['AIN01'])
        background_fit = background['AIN01'][:-1] - robust_fit(background['AIN01'])

        bg_fit = background_fit[:-1] + (robust_fit(signal_fit) - robust_fit(background_fit))

        delta_f = (signal_fit[:-1] - bg_fit) / bg_fit
        return delta_f
    
def get_harp_paths(path, register):
    fpaths = pathlib.Path(path)
    read_path = [path for path in (fpaths.rglob(f"*_{register}_*.bin") )]
    if len(read_path) == 2:
        joined_path = join_binary_files(read_path[0], read_path[1])
        return joined_path
    elif len(read_path) > 2:
        # Look for a joined file
        joined_files = [p for p in fpaths.rglob(f"*_{register}*_joined.bin")]
        if joined_files:
            return joined_files[0]
    elif len(read_path) == 1:
        return read_path[0]
    elif len(read_path) is None:
        raise FileNotFoundError(f"No harp data found for register {register} in {path}.")
      
def join_binary_files(fpath1, fpath2):
    
    out_path = fpath1.parent / f"{fpath1.stem}_joined.bin"
    if out_path.exists():
        print(f"Output file {out_path} already exists. ")
        return out_path
    else:
        with open(out_path, 'wb') as outfile:
            for f in [fpath1, fpath2]:
                with open(f, 'rb') as infile:
                    outfile.write(infile.read())
        return out_path

def apply_butterworth_lowpass_filter(
    demod_signal, low_cut_off=15, fs=10000, order=5
):
    w = low_cut_off / (fs / 2)  # Normalize the frequency
    b, a = butter(order, w, "low")
    output = filtfilt(b, a, demod_signal)
    return output

def robust_fit(trace):
    y = trace
    x = np.arange(len(y)).reshape(-1, 1)
    line_x = np.arange(x.min(), x.max())[:, np.newaxis]
    ransac = linear_model.RANSACRegressor()
    ransac.fit(x, y)
    line_y = ransac.predict(line_x)

    return line_y

