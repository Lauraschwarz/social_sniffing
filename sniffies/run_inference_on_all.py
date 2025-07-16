import subprocess
import pathlib
ROOT_FOLDER = "F:/social_sniffing/rawdata"
OUTPUT_FOLDER = "F:/social_sniffing/derivatives/"

def call_inference_on_all(dest_folder=OUTPUT_FOLDER, ext=".avi"):
    source_folder = pathlib.Path(ROOT_FOLDER)
    fpaths = list(source_folder.rglob(f"*{ext}"))
    for fpath in fpaths:
        relative_path_parent = fpath.relative_to(source_folder).parent
        dest_path = pathlib.Path(dest_folder) / relative_path_parent
        call_inference(fpath, dest_path)
    return fpaths

def call_inference(fpath, dest_folder):
    fpath = pathlib.Path(fpath)
    dest_path = dest_folder / f"{fpath.stem}_inference.slp"
    if dest_path.exists():
        print(f"Skipping {fpath} as {dest_path} already exists.")
        return

    if fpath.exists():
        print(f"processing: {fpath}")
        #command_inf = f"sleap-track -m C:\\Users\\Laura\\PycharmProjects\\sleap\\models\\new_tracks_lesions240708_162312.centroid.n=1201  -m C:\\Users\\Laura\\PycharmProjects\\sleap\\models\\new_tracks_lesions240708_170141.multi_class_topdown.n=1201  -o {dest_path}  --tracking.tracker none {fpath}  "
        command_inf = f"sleap-track -m F:\\sleap_thermistor\\models\\250626_154950.centroid.n=737  -m F:\\sleap_thermistor\\models\\250626_164214.multi_class_topdown.n=737  -o {dest_path}  --tracking.tracker none {fpath}  "
        print(f"{command_inf}")
        subprocess.call(command_inf, shell=True)
        final_dest_path = dest_folder / f"{fpath.stem}.h5"
        command_conv = f"sleap-convert --format analysis -o {final_dest_path} {dest_path} "
        subprocess.call(command_conv, shell=True)

    else:
        print(f'file: {fpath} does not exist; please check your input')

def convert_inference_file(fpath,dest_folder=OUTPUT_FOLDER):
    fpath = pathlib.Path(fpath)
    dest_folder = pathlib.Path(dest_folder)
    dest_path = dest_folder / f"{fpath.stem}.h5"
    if fpath.exists():
        print(f"converting: {fpath}")
        command = f"sleap-convert --format analysis -o {dest_path} {fpath} "
        print(f"{command}")
        subprocess.call(command, shell=True)

    else:
        print(f'file: {fpath} does not exist; please check your input')
def convert_all(dest_folder=OUTPUT_FOLDER, ext=".slp"):
    source_folder = pathlib.Path(ROOT_FOLDER)
    fpaths = list(source_folder.rglob(f"*{ext}"))
    for fpath in fpaths:
        call_inference(fpath, dest_folder)
    return fpaths
call_inference(fpath=pathlib.Path(r'F:\social_sniffing\rawdata\1125131\2025-07-01T12-47-28\Video\1125131.avi'), dest_folder=pathlib.Path(r'F:\social_sniffing\derivatives\1125131\2025-07-01T12-47-28\Video'))
