import harp as hp
import matplotlib
import glob
matplotlib.use('Qt5agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, sosfilt, find_peaks, spectrogram
from scipy.fft import fft, ifft


def create_reader(data_path, mouseID, module, register):
    """
    Create a reader object for the specified data path, datamodule (behaviour/video/stepmotor and harp register.
    """
    file_pattern = f"{data_path}/{module}/{module}_{mouseID}_{register}_*.bin"
    files = glob.glob(file_pattern)
    if not files:
        raise FileNotFoundError(f"No files found for pattern: {file_pattern}")

    return hp.create_reader(files[0], epoch=hp.REFERENCE_EPOCH)

#analog_data = create_reader('F:/harp/2025-04-03T14-58-52', '1124887', 'Behaviour', '44')


# Function to apply moving average filter
def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='same', )

reader = hp.create_reader(r'F:\harp', epoch=hp.REFERENCE_EPOCH)
analog = reader.AnalogData.read(r'Y:\Laura\harp\testing\2025-04-29T12-49-54\behav\behav_testing_44_1904-01-29T22-00-00.bin')


subset = analog.between_time("00:03:44", "00:06:50")


# Extract the analog signal
analog_input = analog['AnalogInput0']
# # Define the Butterworth bandpass filter
#
# # Parameters
# lowcut = 1.0
# highcut = 20.0
# fs = 9600  # Sampling frequency
# sos = butter(1, 20, 'hp', fs=1000, output='sos')
# filtered = sosfilt(sos, analog_input)
# # Filter the analog_input


window_size_25ms = int(0.025 * 9600)
window_size_500ms = int(0.050 * 9600)
smoothed_frequency_500ms = moving_average(analog_input, window_size_25ms)
subtract = analog['AnalogInput0'] - smoothed_frequency_500ms
forward_ewm = subtract.ewm(span=25).mean()
backward_ewm = subtract.iloc[::-1].ewm(span=25).mean().iloc[::-1]
subtract_smooth = (forward_ewm + backward_ewm) / 2
subtract_smooth_forpeaks = subtract_smooth.to_numpy()
peaks, _ = find_peaks(subtract_smooth_forpeaks, prominence=1)

# Calculate time intervals between consecutive peaks and troughs
elapsed_time = (analog_input.index - analog_input.index[0]).total_seconds()
peak_intervals = np.diff(elapsed_time[peaks])#trough_intervals = np.diff(subset.index[troughs])
# Compute frequency as the inverse of the time intervals
peak_frequencies = 1 / peak_intervals
filtered_peak_frequencies = peak_frequencies[(peak_frequencies >= 0.001) & (peak_frequencies <= 20)]
convert_array = pd.Series(filtered_peak_frequencies)
smoothed_peak_frequencies = convert_array.ewm(span=5).mean()
time_for_Hz = subtract_smooth[peaks][1::]
plt.figure(figsize=(10, 6))
plt.plot(analog_input, color='r', marker='o', markersize=1, linewidth=0.5)
plt.show()

port_0 = poke["DIPort0"]
port_1 = poke["DIPort1"]
valve_0 = valve["SupplyPort0"]
valve_1 = valve["SupplyPort1"]
# plt.figure()
# plt.plot(subtract, color='k', linewidth=0.4, marker='o', markersize=1)
# plt.plot(subtract_smooth, color='c', linewidth=0.4, marker='o', markersize=1)
# plt.show()
#plt.plot(time_for_Hz.index, filtered_peak_frequencies, color='r', marker='o', markersize=1, linewidth=0.5)
# # Plotting vertical lines where series is True
for idx in valve_0[valve_0 == True].index:
     plt.axvline(x=idx, color='k', linestyle='solid')

for idx in valve_1[valve_1 == True].index:
    plt.axvline(x=idx, color='k', linestyle='solid')

for idx in port_0[port_0 == True].index:
    plt.axvline(x=idx, color='c', linestyle='dotted')

for idx in port_1[port_1 == True].index:
    plt.axvline(x=idx, color='c', linestyle='dotted')
# #doesnt make sense to take the original time.
plt.ylabel('Frequency (Hz)')
plt.title('Frequency Over Time')
plt.show()
plt.plot(subtract_smooth, color='c', linewidth=0.4, marker='o', markersize=1)
plt.plot(subtract_smooth[peaks], color='r', linewidth=0, marker='o', markersize=2)
plt.show()