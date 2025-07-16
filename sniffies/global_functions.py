import numpy as np
import pandas as pd
import harp as hp
import constants
import pathlib
from scipy.signal import find_peaks, savgol_filter, butter, sosfilt, sosfiltfilt
import matplotlib.pyplot as plt


    
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