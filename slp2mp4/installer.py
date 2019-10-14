import os, sys, shutil
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import tarfile
import configparser

THIS_DIR, _ = os.path.split(os.path.abspath(__file__))
THIS_USER_DIR = os.path.join(THIS_DIR, 'User')

# Paths to external dependencies
FFMPEG_WIN_FOLDER = "ffmpeg-20190914-8efc9fc-win64-static"
FFMPEG_WIN_URL = "https://ffmpeg.zeranoe.com/builds/win64/static/" + FFMPEG_WIN_FOLDER + ".zip"
FM_WIN_FOLDER = "FM-v5.9-Slippi-r18-Win"
FM_WIN_PLAYBACK_CONFIG_FOLDER = "slippi-r18-playback-config"
FM_WIN_URL = "https://www.smashladder.com/download/dolphin/18/Project+Slippi+%28r18%29/windows/32/" + FM_WIN_FOLDER + ".zip"
FM_WIN_PLAYBACK_CONFIG_URL = "https://github.com/project-slippi/Slippi-FM-installer/raw/8bef9c897cbde8bad0ef7afbcb5ada4ab1e6dd94/" + FM_WIN_PLAYBACK_CONFIG_FOLDER + ".tar.gz"


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


def patch_dolphin_sys_game_settings():
    # Remove efb_scale field. This allows selection of resolution options from GFX.ini.
    gal_ini = os.path.join(FM_WIN_FOLDER, "Sys", "GameSettings", "GAL.ini")
    gal_ini_parser = configparser.ConfigParser()
    gal_ini_parser.optionxform = str
    gal_ini_parser.read(gal_ini)
    gal_ini_parser.remove_option('Video_Settings', 'EFBScale')
    gal_ini_fp = open(gal_ini, 'w')
    gal_ini_parser.write(gal_ini_fp)
    gal_ini_fp.close()


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
            recursive_overwrite(THIS_USER_DIR, os.path.join(FM_WIN_FOLDER, "User"))
            recursive_overwrite(os.path.join(FM_WIN_FOLDER, "User"), THIS_USER_DIR)

            # Create the frames folder that dolphin dumps. Dolphin will not dump frames without this
            if not os.path.isdir(os.path.join(THIS_USER_DIR, "Dump", "Frames")):
                os.makedirs(os.path.join(THIS_USER_DIR, "Dump", "Frames"))

            # Create a file to indicate that dependencies are installed and should not be reinstalled
            with open("installed", 'a'):
                os.utime("installed", None)
