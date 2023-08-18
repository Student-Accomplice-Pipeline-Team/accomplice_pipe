import os
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pymelc

shelf_file_prefix = 'shelf_'
shelf_file_ext = '.mel'


def load():
    # Get the paths to any existing shelf files
    shelves_path = Path(__file__).resolve().parent
    shelf_filepaths = [file for file in os.listdir(shelves_path)
                       if file.startswith(shelf_file_prefix) and
                       file.endswith(shelf_file_ext)]

    # Load each shelf
    for filename in shelf_filepaths:
        print(f"Loading {filename}")
        _load_shelf(filename)

    print("Done loading")


def _get_shelf_name(filename: str):
    # Strip the prefix and file extension
    return filename[len(shelf_file_prefix):-len(shelf_file_ext)]


def _load_shelf(filename: str):
    # Get the name of the shelf
    shelf_name = _get_shelf_name(filename)

    # Delete any shelves of the same name
    _delete_shelf(shelf_name)

    # Load the shelf
    mel.eval(f"loadNewShelf {filename}")

    # Create a job to clean up the shelf when Maya exits
    cmds.scriptJob(
        event=['quitApplication',
               f"pipe.shelves._delete_shelf('{shelf_name}')"],
        permanent=True,
    )


def _delete_shelf(name: str):
    # Check if the shelf exists
    if pymelc.shelfLayout(name, exists=True):
        mel.eval(f"silentDeleteShelfTab {name}")
