import os, sys, subprocess, time, shutil, uuid, json
from config import Config

MAX_WAIT_SECONDS = 8 * 60 + 10

class DolphinRunner:

    def __init__(self, conf, user_dir, working_dir, job_id):
        self.conf = conf
        self.user_dir = user_dir
        self.working_dir = working_dir
        self.job_id = job_id

        # get all needed paths
        self.comm_file = os.path.join(self.working_dir, 'slippi-comm-{}.txt'.format(self.job_id))
        self.render_time_file = os.path.join(self.user_dir, 'Logs', 'render_time.txt')
        self.dump_dir = os.path.join(self.user_dir, 'Dump')
        self.frames_dir = os.path.join(self.dump_dir, 'Frames')
        self.audio_dir = os.path.join(self.dump_dir,'Audio')
        self.video_file0 = os.path.join(self.frames_dir, 'framedump0.avi')
        self.video_file1 = os.path.join(self.frames_dir, 'framedump1.avi')
        self.audio_file = os.path.join(self.audio_dir, 'dspdump.wav')

    def count_frames_completed(self):
        num_completed = 0

        if os.path.exists(self.render_time_file):
            with open(self.render_time_file, 'r') as f:
                num_completed = len(list(f))

        print("Rendered ",num_completed," frames")
        return num_completed

    def run(self, slp_file, num_frames):
        """
        Run Dolphin, dumping frames and audio and returning when done
        Returns path_of_video_file, path_of_audio_file
        """
        
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

        # Create a slippi 'comm' file to tell dolphin which file to play
        comm_data = {
            'mode': 'normal',                       # idk
            'replay': slp_file,
            'isRealTimeMode': False,                # idk
            'commandId': str(self.job_id)           # can be any random string, stops dolphin getting confused playing same file twice in a row
        }

        with open(self.comm_file, 'w') as f:
            f.write(json.dumps(comm_data))

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
                raise RuntimeError("Timed out waiting for render")
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

        # Find correct audio and video files
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