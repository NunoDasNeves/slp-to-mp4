# slp to mp4
This script converts [Project Slippi](https://github.com/project-slippi/project-slippi) replay files for  [Super Smash Bros. Melee](https://en.wikipedia.org/wiki/Super_Smash_Bros._Melee) to mp4 videos.

This exists as an alternative to using screen capture software to record the Dolphin window playing back a replay.

## Dependencies

### Linux

Python >= 3.7  
https://www.python.org/downloads/

ffmpeg for encoding the video (if on Linux install with your package manager)  
https://ffmpeg.org/download.html

Slippi-FM-r18 for playing the slippi file and dumping the frames  
https://www.smashladder.com/download/dolphin/18/Project+Slippi+%28r18%29

py-slippi for parsing the slippi file (pip install)  
https://github.com/hohav/py-slippi

A Super Smash Bros. Melee v1.02 NTSC ISO.

### Windows

Python >= 3.7  
https://www.python.org/downloads/

py-slippi for parsing the slippi file (pip install)  
https://github.com/hohav/py-slippi

A Super Smash Bros. Melee v1.02 NTSC ISO.

## Setup

### Linux

Modify the paths in config.json to point to your Melee ISO, ffmpeg binary and the directory of the playback instance of Dolphin.

### Windows

Copy your Super Smash Bros. Melee v1.02 NTSC ISO to SSBMelee.iso in this directory or modify config_windows.json to point to another. Then run the python script and the necessary dependencies will install. If you wish to re-install after the first recording, remove the 'installed' file.

## Usage

```
slp-to-mp4.py REPLAY_FILE [OUTPUT_FILE_OR_DIRECTORY]
```
or
```
slp-to-mp4.py DIRECTORY_WITH_SLP_REPLAYS
```
This launches Dolphin, which plays the replay and dumps frames and audio.  
Then ffmpeg is invoked to combine audio and video.  

If the output file is unspecified, the file will be placed in slp2mp4/out/ and the file name will be the name of the parent directory of the slp file.

## Future work
- Batch jobs - encode multiple replays at a time (maybe a separate script should do this)
- Run Dolphin at higher emulation speed if possible
