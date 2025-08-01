import numpy as np
import pandas as pd
import harp as hp
import constants
import pathlib
from movement.filtering import filter_by_confidence, interpolate_over_time, savgol_filter

import matplotlib.pyplot as plt


    
def get_harp_paths(path, register):
    fpaths = pathlib.Path(path)
    read_path = [path for path in (fpaths.rglob(f"*_{register}*.bin") )]
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
    elif len(read_path) == 0:
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
    
def filter_positions(ds, confidence_threshold=0.39):
        ds.update({
                "position": filter_by_confidence(
                ds.position, ds.confidence, threshold=confidence_threshold,print_report=True)})
        ds.update({
                "position": interpolate_over_time(ds.position, max_gap=50, print_report=True)})
        ds.update(
                {"position": savgol_filter(ds.position, 12)}
)
        return ds

def get_barrier_open_time(fpath):
        reader = hp.create_reader(constants.STEPMOTOR, epoch=hp.REFERENCE_EPOCH)
        fpath = pathlib.Path(fpath) / 'StepMotor'
        read_path = get_harp_paths(fpath, '81')
        if not read_path:
            raise FileNotFoundError("StepMotor file not found.")
        motor_move = reader.Motor0MoveRelative.read(read_path)
        return motor_move['Motor0MoveRelative'].index