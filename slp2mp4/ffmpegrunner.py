import subprocess

class FfmpegRunner:
    def __init__(self, ffmpeg_bin):
        self.ffmpeg_bin = ffmpeg_bin

    def combine(self, concat_file, outfile):
        cmd = [
            self.ffmpeg_bin,
            '-safe', '0',
            '-f', 'concat',             # Set input stream to concatenate
            '-i', concat_file,          # use a concatenation demuxer file which contains a list of files to combine
            '-c', 'copy',               # copy audio and video
            outfile
            ]
        print(' '.join(cmd))
        proc_ffmpeg = subprocess.Popen(args=cmd)
        proc_ffmpeg.wait()

    def run(self, video_file, audio_file, outfile):

        cmd = [
            self.ffmpeg_bin,
            '-y',                   # overwrite output file without asking
            '-i', audio_file,       # 0th input stream: audio
            # offset no longer needed!
            #'-itsoffset', '1.55',   # offset (delay) the audio by 1.55s
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