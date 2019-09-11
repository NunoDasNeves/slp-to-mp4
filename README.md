# slp to mp4
This script converts [Project Slippi](https://github.com/project-slippi/project-slippi) replay files for  [Super Smash Bros. Melee](https://en.wikipedia.org/wiki/Super_Smash_Bros._Melee) to mp4 videos.

This exists as an alternative to using screen capture software to record the Dolphin window playing back a replay.

## Dependencies
This script was written for Linux but may work on Windows too.

Python >= 3.7  
https://www.python.org/downloads/

ffmpeg for encoding the video (if on Linux install with your package manager)  
https://ffmpeg.org/download.html

Slippi-FM-r18 for playing the slippi file and dumping the frames  
https://www.smashladder.com/download/dolphin/18/Project+Slippi+%28r18%29

py-slippi for parsing the slippi file (pip install)  
https://github.com/hohav/py-slippi

A Super Smash Bros. Melee v1.02 NTSC ISO.

## Setup

Modify the paths in config.json to point to your Melee ISO, ffmpeg binary and the directory of the playback instance of Dolphin.

Copy Dolphin.ini and GFX.ini to the playback Dolphin's config directory: `playback/User/Config`. You should back up the existing files in case you want to play slippi replays with the [desktop app](https://github.com/project-slippi/slippi-desktop-app/) later.

## Usage

```
slp-to-mp4.py REPLAY_FILE
```
This launches Dolphin, which plays the replay and dumps frames and audio.  
Then ffmpeg is invoked to combine audio and video.  
An mp4 file with the same name as the replay is created in the slp-to-mp4 directory.

## Future work
- Make interface nicer - specify output file name or directory, show usage etc
- Decrease setup steps - automatically modify and restore Dolphin configuration files
- Batch jobs for running on powerful PCs
- Run Dolphin at higher emulation speed if possible