import os, sys, subprocess, time, shutil, uuid, json, configparser

MAX_WAIT_SECONDS = 8 * 60 + 30
RESOLUTION_DICT = {'480p': '2', '720p': '3', '1080p': '5', '1440p': '6', '2160p': '8'}

class CommFile:
    def __init__(self, comm_path, slp_file, job_id):
        self.comm_data = {
            'mode': 'normal',                       # idk
            'replay': slp_file,
            'isRealTimeMode': False,                # idk
            'commandId': str(job_id)           # can be any random string, stops dolphin getting confused playing same file twice in a row
        }
        self.comm_path = comm_path

    def __enter__(self):
        with open(self.comm_path, 'w') as f:
            f.write(json.dumps(self.comm_data))

    def __exit__(self, type, value, tb):
        os.remove(self.comm_path)
        # Re-raise any exception that occurred in the with block
        if tb is not None:
            return False

class DolphinRunner:

    def __init__(self, conf, base_user_dir, working_dir, job_id):
        self.conf = conf
        self.job_id = job_id
        self.base_user_dir = base_user_dir
        self.user_dir = os.path.join(working_dir, 'User-{}'.format(job_id))

        # Get all needed paths
        self.comm_file = os.path.join(working_dir, 'slippi-comm-{}.txt'.format(self.job_id))
        self.render_time_file = os.path.join(self.user_dir, 'Logs', 'render_time.txt')
        self.dump_dir = os.path.join(self.user_dir, 'Dump')
        self.frames_dir = os.path.join(self.dump_dir, 'Frames')
        self.audio_dir = os.path.join(self.dump_dir,'Audio')
        self.video_file0 = os.path.join(self.frames_dir, 'framedump0.avi')
        self.video_file1 = os.path.join(self.frames_dir, 'framedump1.avi')
        self.audio_file = os.path.join(self.audio_dir, 'dspdump.wav')

    def __enter__(self):
        # Create a new user dir for this job
        shutil.copytree(self.base_user_dir, self.user_dir)
        return self

    def __exit__(self, type, value, tb):
        shutil.rmtree(self.user_dir, ignore_errors=True)
        # Re-raise any exception that occurred in the with block
        if tb is not None:
            return False

    def count_frames_completed(self):
        num_completed = 0

        if os.path.exists(self.render_time_file):
            with open(self.render_time_file, 'r') as f:
                num_completed = len(list(f))

        print("Rendered ",num_completed," frames")
        return num_completed

    def prep_dolphin_settings(self):

        # TODO should we do this?
        # Can't specify separate Sys directory like we can with User, so this would overwrite user's Sys settings
        # We can't remove the option and restore it within dolphinrunner __enter__ and __exit__, because there is a dolphinrunner for each thread in parallel mode
        # - could copy the whole dolphin dir to change this...yuck
        # - could do this in the dolphinrunner caller and restore to the right state
        # - could just clobber this option...
        '''
        # Remove efb_scale field. This allows selection of resolution options from GFX.ini.
        gal_ini = os.path.join(conf.dolphin_dir, "Sys", "GameSettings", "GAL.ini") # need to get sys dir in here
        gal_ini_parser = configparser.ConfigParser()
        gal_ini_parser.optionxform = str
        gal_ini_parser.read(gal_ini)
        gal_ini_parser.remove_option('Video_Settings', 'EFBScale')
        gal_ini_fp = open(gal_ini, 'w')
        gal_ini_parser.write(gal_ini_fp)
        gal_ini_fp.close()
        '''

        # Determine efb_scale value from resolution field in config
        if self.conf.resolution not in RESOLUTION_DICT:
            print("WARNING: configured resolution is not valid, using 480p")
            efb_scale = RESOLUTION_DICT["480p"]
        else:
            efb_scale = RESOLUTION_DICT[self.conf.resolution]

        gfx_ini_path = os.path.join(self.user_dir, "Config", "GFX.ini")
        dolphin_ini_path = os.path.join(self.user_dir, "Config", "Dolphin.ini")
        gale01_ini_path = os.path.join(self.user_dir, "GameSettings", "GALE01.ini")

        # TODO make more of these options adjustable in config.json
        ini_settings = {
            gfx_ini_path: {
                'Settings': [
                    ('EFBScale', efb_scale),

                    # for getting number of frames from file (to tell if we're done)
                    ('LogRenderTimeToFile','True'),

                    # maybe not needed? gives better quality i guess
                    ('DumpCodec', 'H264'),
                    ('BitrateKbps', str(self.conf.bitrateKbps)),
                    ('MSAA', '8'),
                    ('SSAA', 'True')
                ],
                'Enhancements': [
                    ('MaxAnisotropy', '4'),
                    ('TextureScalingType', '1'),
                    ('CompileShaderOnStartup', 'True')
                ]
            },
            dolphin_ini_path: {
                'Interface': [
                    # doesn't render properly with these enabled
                    ('ShowToolbar', 'False'),
                    ('ShowStatusbar', 'False'),
                    ('ShowSeekbar', 'False')
                ],
                'Display': [
                    # high res, convenience
                    ('KeepWindowOnTop', 'True'),
                    ('RenderWindowWidth', '1280'),
                    ('RenderWindowHeight', '1052'),
                    ('RenderWindowAutoSize', 'True')
                ],
                'Core': [
                    # rumble is annoying
                    ('AdapterRumble0', 'False'),
                    ('AdapterRumble1', 'False'),
                    ('AdapterRumble2', 'False'),
                    ('AdapterRumble3', 'False')
                ],
                'Movie': [
                    ('DumpFrames', 'True'),
                    ('DumpFramesSilent', 'True')
                ],
                'DSP': [
                    ('DumpAudio', 'True'),
                    ('DumpAudioSilent', 'True'),
                    # Other audio backends may play sound despite DumpAudioSilent
                    ('Backend', 'ALSA')
                ]
            }
        }

        # If using windows, run all of dolphin in the main window to keep the display cleaner. This breaks in Linux.
        if sys.platform == "win32":
            ini_settings[dolphin_ini_path]['Display'].append(('RenderToMain', "True"))

        if self.conf.widescreen:
            ini_settings[gfx_ini_path]['Settings'].append(('AspectRatio', "6"))

            # kinda hack to figure out what option format we need for widescreen
            # it's this for older versions of slippi:
            widescreen_code = '$Widescreen 16:9'
            with open(gale01_ini_path, 'r') as f:
                # it's this for newer (since rollback? idk, tell me if this breaks)
                if '$Required: Slippi Playback' in f.read():
                    widescreen_code = '$Optional: Widescreen 16:9'

            ini_settings[gale01_ini_path] = {
                'Gecko_Enabled': [
                    (widescreen_code,)
                ]
            }

        for ini_path, opt_dict in ini_settings.items():
            # need these args to ensure Gecko_Enabled options (GALE01.ini) are parsed correctly
            ini_parser = configparser.ConfigParser(allow_no_value=True, delimiters=('=',))

            ini_parser.optionxform = str
            ini_parser.read(ini_path)
            for section, opts in opt_dict.items():
                for opt_tuple in opts:
                    ini_parser.set(section, *opt_tuple)

            ini_fp = open(ini_path, 'w')
            ini_parser.write(ini_fp)
            ini_fp.close()

    def prep_user_dir(self):
        # We need to remove the render time file because we read it to figure out when dolphin is done
        if os.path.exists(self.render_time_file):
            os.remove(self.render_time_file)

        # Remove existing dump files
        if os.path.exists(self.dump_dir):
            shutil.rmtree(self.dump_dir, ignore_errors=True)

        # We have to create 'Frames' and 'Audio' because reasons
        # See Dolphin source: Source/Core/VideoCommon/AVIDump.cpp:AVIDump:CreateVideoFile() - it doesn't create the thing
        # TODO: patch Dolphin I guess
        os.makedirs(self.frames_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)

    def get_dump_files(self):
        """
        Find correct audio and video files after Dolphin has dumped them
        """
        if not os.path.exists(self.audio_file):
            raise RuntimeError("Audio dump missing!")

        if not os.path.exists(self.video_file1):
            if not os.path.exists(self.video_file0):
                raise RuntimeError("Frame dump missing!")
            video_file = self.video_file0
        else:
            video_file = self.video_file1
        audio_file = self.audio_file

        return video_file, audio_file

    def run(self, slp_file, num_frames):
        """
        Run Dolphin, dumping frames and audio and returning when done
        Returns path_of_video_file, path_of_audio_file
        """

        self.prep_dolphin_settings()
        self.prep_user_dir()

        # Create a slippi 'comm' file to tell dolphin which file to play
        with CommFile(self.comm_file, slp_file, self.job_id):

            # Construct command string and run dolphin
            cmd = [
                self.conf.dolphin_bin,
                '-i', self.comm_file,       # The comm file tells dolphin which slippi file to play (see above)
                '-b',                       # Exit dolphin when emulation ends
                '-e', self.conf.melee_iso,  # ISO to use
                '-u', self.user_dir         # specify User dir
                ]
            print(' '.join(cmd))
            # TODO run faster than realtime if possible
            proc_dolphin = subprocess.Popen(args=cmd)

            # Poll file until done
            start_timer = time.perf_counter()
            while self.count_frames_completed() < num_frames:

                if time.perf_counter() - start_timer > MAX_WAIT_SECONDS:
                    print("WARNING: Timed out waiting for render")
                    break

                if proc_dolphin.poll() is not None:
                    print("WARNING: Dolphin exited before replay finished - may not have recorded entire replay")
                    break

                time.sleep(1)

            # Kill dolphin
            proc_dolphin.terminate()
            try:
                proc_dolphin.wait(timeout=5)
            except subprocess.TimeoutExpired as t:
                print ("Warning: timed out waiting for Dolphin to terminate")
                proc_dolphin.kill()

        return self.get_dump_files()