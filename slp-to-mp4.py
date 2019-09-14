#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid
from pathlib import Path
from slippi import Game
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import tarfile

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
MIN_GAME_LENGTH = 30 * 60
FPS = 60
JOB_ID = uuid.uuid4()

# Paths to external dependencies
FFMPEG_WIN_FOLDER = "ffmpeg-20190914-8efc9fc-win64-static"
FFMPEG_WIN_URL = "https://ffmpeg.zeranoe.com/builds/win64/static/" + FFMPEG_WIN_FOLDER + ".zip"
FM_WIN_FOLDER = "FM-v5.9-Slippi-r18-Win"
FM_WIN_PLAYBACK_CONFIG_FOLDER = "slippi-r18-playback-config"
FM_WIN_URL = "https://www.smashladder.com/download/dolphin/18/Project+Slippi+%28r18%29/windows/32/" + FM_WIN_FOLDER + ".zip"
FM_WIN_PLAYBACK_CONFIG_URL = "https://github.com/project-slippi/Slippi-FM-installer/raw/8bef9c897cbde8bad0ef7afbcb5ada4ab1e6dd94/" + FM_WIN_PLAYBACK_CONFIG_FOLDER + ".tar.gz"

# Paths to files in (this) script's directory
SCRIPT_DIR, _ = os.path.split(os.path.abspath(sys.argv[0]))
if sys.platform == "win32":
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config_windows.json')
else:
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
            self.remove_short = j['remove_short']

        if sys.platform == "win32":
            self.dolphin_bin = str(Path(self.dolphin_dir, 'Dolphin'))
        else:
            self.dolphin_bin = str(Path(self.dolphin_dir, 'dolphin-emu'))
        self.render_time_file = str(Path(self.dolphin_dir, 'User', 'Logs', 'render_time.txt'))
        self.dump_dir = str(Path(self.dolphin_dir, 'User', 'Dump'))
        self.frames_dir = str(Path(self.dump_dir, 'Frames'))
        self.audio_dir = str(Path(self.dump_dir, 'Audio'))
        self.video_file0 = str(Path(self.frames_dir, 'framedump0.avi'))
        self.video_file1 = str(Path(self.frames_dir, 'framedump1.avi'))
        self.audio_file = str(Path(self.audio_dir, 'dspdump.wav'))

def recursive_overwrite(src, dest, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f),
                                    os.path.join(dest, f),
                                    ignore)
    else:
        shutil.copyfile(src, dest)

def installDependencies():
    if sys.platform == "win32":
        if not os.path.exists("installed"):
            print("Installing dependencies for Windows")

            # Retrieve ffmpeg
            response = urllib.request.Request(FFMPEG_WIN_URL, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(response).read()
            f = ZipFile(BytesIO(data))
            print(f.namelist())
            if os.path.exists(FFMPEG_WIN_FOLDER):
                shutil.rmtree(FFMPEG_WIN_FOLDER)
            f.extractall()

            # Retrieve Dolphin (FM)
            response = urllib.request.Request(FM_WIN_URL, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(response).read()
            f = ZipFile(BytesIO(data))
            print(f.namelist())
            if os.path.exists(FM_WIN_FOLDER):
                shutil.rmtree(FM_WIN_FOLDER)
            f.extractall()

            # Retrieve Slippi playback configuration
            response = urllib.request.Request(FM_WIN_PLAYBACK_CONFIG_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with open(FM_WIN_PLAYBACK_CONFIG_FOLDER + ".tar.gz", "wb") as out_file:
                out_file.write(urllib.request.urlopen(response).read())
            f = tarfile.open(FM_WIN_PLAYBACK_CONFIG_FOLDER + ".tar.gz", mode='r:gz')
            print(f.getnames())
            try:
                shutil.rmtree(FM_WIN_PLAYBACK_CONFIG_FOLDER)
            except Exception:
                os.makedirs(FM_WIN_PLAYBACK_CONFIG_FOLDER)
            f.extractall(FM_WIN_PLAYBACK_CONFIG_FOLDER)
            f.close()
            os.remove(FM_WIN_PLAYBACK_CONFIG_FOLDER + ".tar.gz")

            # Overwrite playback configuration onto dolphin
            recursive_overwrite(os.path.join(FM_WIN_PLAYBACK_CONFIG_FOLDER, "Binaries"), FM_WIN_FOLDER)
            shutil.rmtree(FM_WIN_PLAYBACK_CONFIG_FOLDER)

            # Overwrite GFX and Dolphin ini from slp-to-mp4
            shutil.copy2(THIS_GFX_INI, os.path.join(os.path.join(os.path.join(FM_WIN_FOLDER, "User"), "Config"), "GFX.ini"))
            shutil.copy2(THIS_DOLPHIN_INI, os.path.join(os.path.join(os.path.join(FM_WIN_FOLDER, "User"), "Config"), "Dolphin.ini"))

            # Create the frames folder that dolphin dumps. Dolphin will not dump frames without this
            os.makedirs(os.path.join(os.path.join(os.path.join(FM_WIN_FOLDER, "User"), "Dump"), "Frames"))

            # Create a file to indicate that dependencies are installed and should not be reinstalled
            with open("installed", 'a'):
                os.utime("installed", None)

def is_game_too_short(num_frames, remove_short):
    return num_frames < MIN_GAME_LENGTH and remove_short

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
    if is_game_too_short(num_frames, conf.remove_short):
        print("Warning: Game is less than 30 seconds and won't be recorded. Override in config.")
        return

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
    # TODO Investigate if running faster than realtime and encoding to 60 Hz has higher throughput than batch recording.
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
    if not os.path.exists(conf.video_file1):
        if not os.path.exists(conf.video_file0):
            raise RuntimeError("Frame dump missing!")
        shutil.move(conf.video_file0, VIDEO_IN_FILE)
    else:
        shutil.move(conf.video_file1, VIDEO_IN_FILE)
    shutil.move(conf.audio_file, AUDIO_IN_FILE)


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
    installDependencies()
    main()
