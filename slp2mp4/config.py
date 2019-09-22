import os, json, sys

THIS_DIR, _ = os.path.split(os.path.abspath(__file__))

if sys.platform == "win32":
    THIS_CONFIG = os.path.join(THIS_DIR, 'config_windows.json')
    DOLPHIN_NAME = 'Dolphin.exe'
else:
    THIS_CONFIG = os.path.join(THIS_DIR, 'config.json')
    DOLPHIN_NAME = 'dolphin-emu'

THIS_USER_DIR = os.path.join(THIS_DIR, 'User')

class Config:
    def __init__(self):
        with open(THIS_CONFIG, 'r') as f:
            j = json.loads(f.read())
            self.melee_iso = os.path.expanduser(j['melee_iso'])
            self.check_path(self.melee_iso)
            self.dolphin_dir = os.path.expanduser(j['dolphin_dir'])
            self.check_path(self.dolphin_dir)
            self.ffmpeg = os.path.expanduser(j['ffmpeg'])
            self.remove_short = j['remove_short']

        self.dolphin_bin = os.path.join(self.dolphin_dir, DOLPHIN_NAME)
        self.render_time_file = os.path.join(THIS_USER_DIR, 'Logs', 'render_time.txt')
        self.dump_dir = os.path.join(THIS_USER_DIR, 'Dump')
        self.check_path(self.ffmpeg)
        self.check_path(self.dolphin_bin)
        self.frames_dir = os.path.join(self.dump_dir, 'Frames')
        self.audio_dir = os.path.join(self.dump_dir, 'Audio')
        self.video_file0 = os.path.join(self.frames_dir, 'framedump0.avi')
        self.video_file1 = os.path.join(self.frames_dir, 'framedump1.avi')
        self.audio_file = os.path.join(self.audio_dir, 'dspdump.wav')

    def check_path(self, path):
        if not os.path.exists(path):
            raise RuntimeError("{} does not exist".format(path))
