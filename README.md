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

psutil for finding number of physical cores
https://github.com/giampaolo/psutil

A Super Smash Bros. Melee v1.02 NTSC ISO.

### Windows

Python >= 3.7  
https://www.python.org/downloads/

py-slippi for parsing the slippi file (pip install)  
https://github.com/hohav/py-slippi

psutil for finding number of physical cores
https://github.com/giampaolo/psutil

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

---
If recording one replay file with no output file specified, the video file with the same name will be placed in slp2mp4/out.

---
If recording a directory and not combining, the individual games will be placed in a subfolder in slp2mp4/out/ with the .slp parent folder's name. Example:
```
Name_Of_Event/Game_1234.slp
Name_Of_Event/Set_A/Game_1234.slp
Name_Of_Event/Set_A/Game_1235.slp
```
gives
```
slp2mp4/out/Name_Of_Event/Game_1234.mp4
slp2mp4/out/Set_A/Game_1234.mp4
slp2mp4/out/Set_A/Game_1235.mp4
```

---
If recording a directory and combining, one video will be created in slp2mp4/out/ for each subdirectory with the .slp parent folder's name. Example:

```
Name_Of_Event/Game_1234.slp
Name_Of_Event/Set_A/Game_1234.slp
Name_Of_Event/Set_A/Game_1235.slp
```
gives
```
slp2mp4/out/Name_Of_Event.mp4
slp2mp4/out/Set_A.mp4
```

## Performance
Resolution, widescreen, bitrate, and the number of parallel games will all affect performance. Dolphin will not record well (skips additional frames) when running less than or greater than 60 FPS. It becomes noticeable below 58 FPS. YouTube requires a resolution of at least 720p to upload a 60 FPS video, so it should be a goal to run at that resolution or higher. A higher bitrate will come with better video quality but larger file size and worse performance because dolphin has more to encode. The number of parallel games will have the largest effect on performance. The 'recommended' value is the number of physical cpu cores, but greater or fewer parallel games may be optimal.

## Future work
- Multiprocessing
  - Allow combining after all required files are done recording while multiprocessing
  - Better progress reporting
  - Warning on completion if average runtime frame rate is below 58 fps
- Run Dolphin at higher emulation speed if possible
- GUI
