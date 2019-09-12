#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid
from pathlib import Path
from slippi import Game

USAGE = """\
slp-to-mp4 - convert slippi files to mp4 videos

USAGE: slp-to-mp4.py REPLAY_FILE [OUT_FILE]

Notes:
This script requires a config.json, Dolphin.ini and GFX.ini in the same directory
OUT_FILE can be a directory or a file name ending in .mp4, or omitted.
e.g.
This will create my_replay.mp4 in the current directory:
 $ slp-to-mp4.py my_replay.slp

This will create my_video.mp4 in the current directory:
 $ slp-to-mp4.py my_replay.slp my_video.mp4

This will create videos/my_replay.mp4, creating the videos directory if it doesn't exist
 $ slp-to-mp4.py my_replay.slp videos
"""

MAX_WAIT_SECONDS = 8 * 60 + 10
FPS = 60
JOB_ID = uuid.uuid4()

# Paths to files in (this) script's directory
SCRIPT_DIR, _ = os.path.split(os.path.abspath(sys.argv[0]))
THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config.json')
THIS_DOLPHIN_INI = os.path.join(SCRIPT_DIR, 'Dolphin.ini')
THIS_GFX_INI = os.path.join(SCRIPT_DIR, 'GFX.ini')
COMM_FILE = os.path.join(SCRIPT_DIR, 'slippi-comm-{}.txt'.format(JOB_ID))
AUDIO_IN_FILE = os.path.join(SCRIPT_DIR, 'audio-{}.audio'.format(JOB_ID))
VIDEO_IN_FILE = os.path.join(SCRIPT_DIR, 'video-{}.video'.format(JOB_ID))

class Config:
    def __init__(self):
        with open(THIS_CONFIG, 'r') as f:
            j = json.loads(f.read())
            self.melee_iso = os.path.expanduser(j['melee_iso'])
            self.dolphin_dir = os.path.expanduser(j['dolphin_dir'])
            self.ffmpeg = os.path.expanduser(j['ffmpeg'])

        self.dolphin_bin = str(Path(self.dolphin_dir, 'dolphin-emu'))
        self.render_time_file = str(Path(self.dolphin_dir, 'User', 'Logs', 'render_time.txt'))
        self.dump_dir = str(Path(self.dolphin_dir, 'User', 'Dump'))
        self.frames_dir = str(Path(self.dump_dir, 'Frames'))
        self.audio_dir = str(Path(self.dump_dir,'Audio'))
        self.video_file = str(Path(self.frames_dir, 'framedump1.avi'))
        self.audio_file = str(Path(self.audio_dir, 'dspdump.wav'))

def count_frames_completed(conf):
    num_completed = 0

    if os.path.exists(conf.render_time_file):
        with open(conf.render_time_file, 'r') as f:
            num_completed = len(list(f))

    print("Rendered ",num_completed," frames")
    return num_completed

def main():

    # Some basic checks before continuing

    if not (os.path.exists(THIS_CONFIG) and os.path.exists(THIS_DOLPHIN_INI) and os.path.exists(THIS_GFX_INI)):
        print(USAGE)
        sys.exit()

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

    # Parse file with py-slippi to determine number of frames
    slippi_game = Game(slp_file)
    num_frames = slippi_game.metadata.duration

    # We need to remove the render time file because we read it to figure out when dolphin is done
    print("Removing", conf.render_time_file)
    if os.path.exists(conf.render_time_file):
        os.remove(conf.render_time_file)

    # Remove existing dump files
    print("Removing", conf.dump_dir)
    for path in os.listdir(conf.dump_dir):
        shutil.rmtree(path, ignore_errors=True)

    # TODO Dolphin.ini, GFX.ini stuff

    # Create a slippi 'comm' file to tell dolphin which file to play
    comm_data = {
        'mode': 'normal',                       # idk
        'replay': slp_file,
        'isRealTimeMode': False,                # idk
        'commandId': '6ab7afc9916602b43bf43f1b' # can be any random string, stops dolphin getting confused playing same file twice in a row
    }

    with open(COMM_FILE, 'w') as f:
        f.write(json.dumps(comm_data))

    # ####################################################
    # Run Dolphin and dump frames

    # Construct command string and run dolphin
    cmd = [
        conf.dolphin_bin,
        '-i', COMM_FILE,        # The comm file tells dolphin which slippi file to play (see above)
        '-b',                   # Exit dolphin when emulation ends
        '-e', conf.melee_iso    # ISO to use
        ]
    print(' '.join(cmd))
    # TODO run faster than realtime if possible
    proc_dolphin = subprocess.Popen(args=cmd)

    # Poll file until done
    start_timer = time.perf_counter()
    while count_frames_completed(conf) < num_frames:
        if time.perf_counter() - start_timer > MAX_WAIT_SECONDS:
            raise RuntimeError("Timed out waiting for render")
        time.sleep(1)

    # Kill dolphin
    proc_dolphin.terminate()
    try:
        proc_dolphin.wait(timeout=5)
    except subprocess.TimeoutExpired as t:
        print ("Warning: timed out waiting for Dolphin to terminate")
        proc_dolphin.kill()

    # ####################################################
    # Encode

    # Move audio and video files to cwd
    if not os.path.exists(conf.audio_file):
        raise RuntimeError("Audio dump missing!")
    if not os.path.exists(conf.video_file):
        raise RuntimeError("Frame dump missing!")
    shutil.move(conf.audio_file, AUDIO_IN_FILE)
    shutil.move(conf.video_file, VIDEO_IN_FILE)

    # Convert audio and video to video
    cmd = [
        conf.ffmpeg,
        '-y',                   # overwrite output file without asking
        '-i', AUDIO_IN_FILE,    # 0th input stream: audio
        '-itsoffset', '1.55',   # offset (delay) the audio by 1.55s
        '-i', VIDEO_IN_FILE,    # 1st input stream: video
        '-map', '1:v',          # map 1st input to video output
        '-map', '0:a',          # map 0th input to audio output
        '-c:a', 'mp3',          # convert audio encoding to mp3 for output
        '-c:v', 'copy',         # use the same encoding (avi) for video output
        outfile
        ]
    print(' '.join(cmd))
    proc_ffmpeg = subprocess.Popen(args=cmd)
    proc_ffmpeg.wait()

    os.remove(AUDIO_IN_FILE)
    os.remove(VIDEO_IN_FILE)
    os.remove(COMM_FILE)

    print('Created {}'.format(outfile))

if __name__ == '__main__':
    main()
