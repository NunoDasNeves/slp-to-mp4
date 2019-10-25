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

## Configuration
For linux, the configuration file is config.json. For Windows, the file is config_windows.json. 
- 'melee_iso' is the path to your Super Smash Bros. Melee 1.02 ISO. 
- 'dolphin_dir' and 'ffmpeg' in linux need to be set to the playback path in the installed version of dolphin, and the default installed path of ffmpeg. In windows, these dependencies are downloaded and installed in the local directory so there is no need to change the paths
- 'resolution' can be set to the following. The output resolution is the minimum resolution dolphin can run above the resolution in this configuration.
  - 480p
  - 720p
  - 1080p
  - 1440p
  - 2160p
- 'widescreen' can be true or false. Enabling will set the resolution to 16:9
- 'bitrateKbps' must be a number. It selects the bitrate in Kilobits per second that dolphin records at.
- 'parallel_games' must be a number greater than 0 or "recommended". This is the maximum number of games that will run at the same time. "recommended" will select the number of physical cores in the CPU.
- 'remove_short' can be true or false. Enabling will not record games less than 30 seconds. Most games less than 30 seconds are handwarmers, so it can save time not to record them.
- 'combine': can be true or false, and matters only when recording a folder of .slp files. If false, the .mp4 files will be left in their subfolders in the output folder. If true, each subfolder of .mp4 files will be combined into .mp4 files in the output folder.

## Performance
Resolution, widescreen, bitrate, and the number of parallel games will all affect performance. Dolphin will not record well (skips additional frames) when running less than or greater than 60 FPS. It becomes noticeable below 58 FPS. YouTube requires a resolution of at least 720p to upload a 60 FPS video, so it should be a goal to run at that resolution or higher. A higher bitrate will come with better video quality but larger file size and worse performance because dolphin has more to encode. The number of parallel games will have the largest effect on performance. The 'recommended' value is the number of physical cpu cores, but greater or fewer parallel games may be optimal.

## Future work
- Multiprocessing
  - Allow combining after all required files are done recording while multiprocessing
  - Better progress reporting
  - Warning on completion if average runtime frame rate is below 58 fps
- Run Dolphin at higher emulation speed if possible
- GUI
