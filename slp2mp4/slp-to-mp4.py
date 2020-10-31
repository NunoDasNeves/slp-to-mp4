#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid, multiprocessing, psutil, glob
from pathlib import Path
from slippi import Game
from config import Config
from dolphinrunner import DolphinRunner
from ffmpegrunner import FfmpegRunner

VERSION = '1.0.0'
USAGE = """\
slp-to-mp4 {}
Convert slippi files to mp4 videos

USAGE: slp-to-mp4.py REPLAY_FILE [OUT_FILE]

Notes:
OUT_FILE can be a directory or a file name ending in .mp4, or omitted.
e.g.
This will create my_replay.mp4 in the current directory:
 $ slp-to-mp4.py my_replay.slp

This will create my_video.mp4 in the current directory:
 $ slp-to-mp4.py my_replay.slp my_video.mp4

This will create videos/my_replay.mp4, creating the videos directory if it doesn't exist
 $ slp-to-mp4.py my_replay.slp videos

See README.md for details
""".format(VERSION)

FPS = 60
MIN_GAME_LENGTH = 30 * FPS
DURATION_BUFFER = 70              # Record for 70 additional frames

# Paths to files in (this) script's directory
SCRIPT_DIR, _ = os.path.split(os.path.abspath(__file__))
if sys.platform == "win32":
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config_windows.json')
else:
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config.json')
OUT_DIR = os.path.join(SCRIPT_DIR, 'out')


combined_files = []


def is_game_too_short(num_frames, remove_short):
    return num_frames < MIN_GAME_LENGTH and remove_short


def get_num_processes(conf):
    if conf.parallel_games == "recommended":
        return psutil.cpu_count(logical=False)
    else:
        return int(conf.parallel_games)


def clean():
    for folder in glob.glob("User-*"):
        shutil.rmtree(folder)
    for file in glob.glob("slippi-comm-*"):
        os.remove(file)

# Evaluate whether file should be run. The open in dolphin and combine video and audio with ffmpeg.
def record_file_slp(slp_file, outfile):
    conf = Config()

    # Parse file with py-slippi to determine number of frames
    slippi_game = Game(slp_file)
    num_frames = slippi_game.metadata.duration + DURATION_BUFFER

    if is_game_too_short(slippi_game.metadata.duration, conf.remove_short):
        print("Warning: Game is less than 30 seconds and won't be recorded. Override in config.")
        return

    DOLPHIN_USER_DIR = os.path.join(conf.dolphin_dir, 'User')
    # Dump frames
    with DolphinRunner(conf, DOLPHIN_USER_DIR, SCRIPT_DIR, uuid.uuid4()) as dolphin_runner:
        video_file, audio_file = dolphin_runner.run(slp_file, num_frames)

        # Encode
        ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
        ffmpeg_runner.run(video_file, audio_file, outfile)

        print('Created {}'.format(outfile))


# In the out folder, run through each subdirectory and count the number of mp4 files. Add these files to
# concat_file.txt. ffmpeg uses this to combine the mp4 files.
def combine(conf):
    for subdir, dirs, files in os.walk(OUT_DIR, topdown=False):
        basedir = os.path.basename(subdir)
        if os.path.exists(os.path.join(subdir, 'concat_file.txt')):
            os.remove(os.path.join(subdir, 'concat_file.txt'))
        file_count = 0
        with open(os.path.join(subdir, 'concat_file.txt'), 'w+') as concat_file:
            lines = []

            # Count the number of MP4 files that weren't written using the combine function
            for file in files:
                try:
                    if file.endswith('.mp4') and os.path.join(subdir, file) not in combined_files:
                        file_count = file_count + 1

                        # Append to lines
                        lines.append("file \'" + os.path.join(subdir, file) + "\'" + "\n")
                except Exception:
                    pass

            # Write lines to the concat_file
            concat_file.writelines(lines)

        # If there is 1 or more mp4 file and not overwriting an existing file
        if file_count > 0 and not os.path.exists(os.path.join(OUT_DIR, basedir) + '.mp4'):
            ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
            ffmpeg_runner.combine(os.path.join(subdir, 'concat_file.txt'), os.path.join(OUT_DIR, basedir) + '.mp4')
            combined_files.append(os.path.join(OUT_DIR, basedir) + '.mp4')

            # Remove subdirectory after combined
            if os.path.exists(os.path.join(OUT_DIR, basedir)) and os.path.exists(os.path.join(OUT_DIR, basedir) + '.mp4'):
                shutil.rmtree(os.path.join(OUT_DIR, basedir))
        if os.path.exists(os.path.join(subdir, 'concat_file.txt')):
            os.remove(os.path.join(subdir, 'concat_file.txt'))


# Get a list of the input files and their subdirectories to prepare the output files. Feed this to record_file_slp.
# If combine is true, combine the files in the out folder every time there is a new subdirectory.
def record_folder_slp(slp_folder, conf):
    in_files = []
    out_files = []

    # Get a list of the input files and their subdirectories. The output file will use the basename of the subdirectory
    # and the name of the file without the extension
    for subdir, dirs, files in os.walk(slp_folder):
        for file in files:
            if file.endswith('.slp'):
                in_files.append([subdir, file])
                out_files.append([os.path.basename(subdir), str(file.split('.')[:-1][0]) + '.mp4'])

    if len(out_files) == 0:
        RuntimeError("No slp files in folder!")
    last_dir = out_files[0][0]
    args = []
    for index, in_file in enumerate(in_files):

        # Combine last subdirectory on discovery of a new subdirectory
        if out_files[index][0] != last_dir:
            if conf.combine:
                #combine(conf)
                # TODO: Find a way to fix combining folders while still multiprocessing
                pass
            last_dir = out_files[index][0]

        # Make the needed directory in the output
        if not os.path.isdir(os.path.join(OUT_DIR, out_files[index][0])):
            os.makedirs(os.path.join(OUT_DIR, out_files[index][0]))

        # Record the single slp file
        slp_file = os.path.join(in_file[0], in_file[1])
        out_file = os.path.join(OUT_DIR, out_files[index][0], out_files[index][1])
        if not os.path.exists(out_file):
            args.append((slp_file, out_file))

    num_processes = get_num_processes(conf)

    pool = multiprocessing.Pool(processes=num_processes)
    pool.starmap(record_file_slp, args)
    pool.close()

    # Combine one last time
    if conf.combine:
        combine(conf)


def main():

    # Parse arguments

    if len(sys.argv) == 1 or '-h' in sys.argv:
        print(USAGE)
        sys.exit()

    slp_file = os.path.abspath(sys.argv[1])
    clean()
    os.makedirs(OUT_DIR, exist_ok=True)

    # Handle all the outfile argument possibilities
    outfile = ''
    if len(sys.argv) > 2:
        outfile_name = ''
        outdir = ''
        if sys.argv[2].endswith('.mp4'):
            outdir, outfile_name = os.path.split(sys.argv[2])
        else:
            outdir = sys.argv[2]
            outfile_name, _ = os.path.splitext(os.path.basename(slp_file))
            outfile_name += '.mp4'

        # We need to remove '..' etc from the path before making directories
        outdir = os.path.abspath(outdir)
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, outfile_name)
    else:
        outfile, _ = os.path.splitext(os.path.basename(slp_file))
        outfile += '.mp4'
        outfile = os.path.join(OUT_DIR, outfile)

    if os.path.isdir(slp_file):
        conf = Config()
        record_folder_slp(slp_file, conf)
    else:
        record_file_slp(slp_file, outfile)


if __name__ == '__main__':
    main()
