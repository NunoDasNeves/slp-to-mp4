#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid
from pathlib import Path
from slippi import Game
from config import Config
from installer import installDependencies
from dolphinrunner import DolphinRunner

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

MIN_GAME_LENGTH = 30 * 60
FPS = 60
JOB_ID = uuid.uuid4()

# Paths to files in (this) script's directory
SCRIPT_DIR, _ = os.path.split(os.path.abspath(__file__))
if sys.platform == "win32":
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config_windows.json')
else:
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config.json')
THIS_USER_DIR = os.path.join(SCRIPT_DIR, 'User')
COMM_FILE = os.path.join(SCRIPT_DIR, 'slippi-comm-{}.txt'.format(JOB_ID))

def is_game_too_short(num_frames, remove_short):
    return num_frames < MIN_GAME_LENGTH and remove_short

def main():

    # Parse arguments

    if len(sys.argv) == 1 or '-h' in sys.argv:
        print(USAGE)
        sys.exit()

    slp_file = os.path.abspath(sys.argv[1])

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

    # ####################################################
    # Set up files, load config etc

    conf = Config()

    dolphin_runner = DolphinRunner(conf, THIS_USER_DIR, SCRIPT_DIR, JOB_ID)

    # Parse file with py-slippi to determine number of frames
    slippi_game = Game(slp_file)
    num_frames = slippi_game.metadata.duration
    if is_game_too_short(num_frames, conf.remove_short):
        print("Warning: Game is less than 30 seconds and won't be recorded. Override in config.")
        return

    video_file, audio_file = dolphin_runner.run(slp_file, num_frames)

    # ####################################################
    # Encode

    # Convert audio and video to video
    cmd = [
        conf.ffmpeg,
        '-y',                   # overwrite output file without asking
        '-i', audio_file,  # 0th input stream: audio
        '-itsoffset', '1.55',   # offset (delay) the audio by 1.55s
        '-i', video_file,  # 1st input stream: video
        '-map', '1:v',          # map 1st input to video output
        '-map', '0:a',          # map 0th input to audio output
        '-c:a', 'mp3',          # convert audio encoding to mp3 for output
        '-c:v', 'copy',         # use the same encoding (avi) for video output
        outfile
        ]
    print(' '.join(cmd))
    proc_ffmpeg = subprocess.Popen(args=cmd)
    proc_ffmpeg.wait()

    os.remove(COMM_FILE)

    print('Created {}'.format(outfile))

if __name__ == '__main__':
    installDependencies()
    main()
