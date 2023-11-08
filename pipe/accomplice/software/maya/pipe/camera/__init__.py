"""Camera tools for Stumaya"""

import logging
import os
import shutil
from pathlib import Path

import maya.cmds as cmds
import pymel.core as pm
from pxr import Sdf

import pipe

# TODO: Get frame range from shotgrid

CAMERA_DIR = "camera"

log = logging.getLogger(__name__)


def _shot_select_gui():
    shot_list = sorted(pipe.server.get_shot_list())

    if cmds.window("ms_selectShot_GUI", exists=True):
        cmds.deleteUI("ms_selectShot_GUI")

    win = cmds.window("ms_selectShot_GUI", title="Select Shot")
    cmds.showWindow(win)
    # cmds.rowLayout(numberOfColumns=1, adjustableColumn=1, rowAttach=[1, 'both', 0])
    cmds.columnLayout(adjustableColumn=True)

    cmds.rowLayout(numberOfColumns=3, adjustableColumn=1)
    prefix = cmds.textFieldGrp("search_field", adjustableColumn=1)
    cmds.button(label="Search", c=lambda x: print("search"))
    cmds.button(label="X", c=lambda x: print("base_list"))
    cmds.setParent("..")

    selection = cmds.textScrollList(
        "Shot_List",  # numberOfRows=8,
        append=shot_list,
        selectIndexedItem=1,
        showIndexedItem=1,
    )

    cmds.rowLayout(numberOfColumns=2)
    cmds.button(label="Select Current Shot", c=lambda x: print("hello"))
    cmds.button(label="Next", c=lambda x: print("goodbye"))
    cmds.setParent("..")


def export(shot: str = None):
    # Detect all cameras
    cameras = cmds.ls(type=("camera"), l=True)

    user_cameras = [
        camera
        for camera in cameras
        if not cmds.camera(
            cmds.listRelatives(camera, parent=True)[0], startupCamera=True, q=True
        )
    ]

    if len(user_cameras) > 1:
        confirm = cmds.confirmDialog(
            title="Could not export shot camera",
            message="More than one camera detected in scene",
            button=["Ok"],
            defaultButton="Ok",
            dismissString="Other",
        )
        return 1

    _shot_select_gui()

    # if confirm == "Ok":
    #    pass

    print(user_cameras)

    # Prompt the user if the shot hasn't been specified
    if not shot:
        pass


# def check_if_selected(self):
#    curr_selection = cmds.ls(selection=True)
#    if len(curr_selection) == 0:
#        confirm = cmds.confirmDialog(title='WARNING', message="Nothing is selected", button=['Ok'],
#                                        defaultButton='Ok', dismissString='Other')
#        if confirm == "Ok":
#            pass
#    else:
#        self.shot_select_gui()
#
# Receives a textScrollList and returns the currently selected list item
# def getSelected(self, scrollList):
#    selected = cmds.textScrollList(scrollList, q=1, si=1)
#    return selected
#
# This is a GUI that presents four options of what you are exporting. The one selected will determine the location that the object is created in
# def shot_select_gui(self):
#    shot_list = pipe.server.get_shot_list()
#
#    if cmds.window("ms_selectShot_GUI", exists=True):
#        cmds.deleteUI("ms_selectShot_GUI")
#
#    win = cmds.window("ms_selectObject_GUI", title="SELECT OBJECT GUI")
#    cmds.showWindow(win)
#    cmds.columnLayout()
#
#    selection = cmds.textScrollList( "Shot_List", numberOfRows=8,
#                    append=shot_list,
#                    selectIndexedItem=1, showIndexedItem=1)
#
#    cmds.rowLayout(numberOfColumns=1)
#    cmds.button(label="Next", c=lambda x: self.save_object(self.getSelected(selection)[0]))
#    cmds.setParent("..")
#
# Stores the selected object in a variable to be used later. Triggers a text prompt if "other" was selected. Else triggers the Shot select gui
# def save_object(self, selected_object):
#    self.object_selection = selected_object
#
#    if self.object_selection == "other":
#        self.other_object_gui()
#    else:
#        self.shot_select_gui()
#
# Stores the selected shot in a variable to be used later and triggers the framerange gui
# def save_shot(self, selected_shot):
#    self.shot_selection = selected_shot
#    self.get_frameRange_gui()
#
#    if cmds.window("ms_selectShot_GUI", exists=True):
#            cmds.deleteUI("ms_selectShot_GUI")
#
#    #self.exporter()
#
# This GUI shows a list of the shots to select
# def shot_select_gui(self):
#    self.shot_list = pipe.server.get_shot_list()
#    self.shot_list = sorted(self.shot_list)
#
#    if cmds.window("ms_selectObject_GUI", exists=True):
#            cmds.deleteUI("ms_selectObject_GUI")
#
#    if cmds.window("ms_selectShot_GUI", exists=True):
#            cmds.deleteUI("ms_selectShot_GUI")
#
#    win = cmds.window("ms_selectShot_GUI", title="SELECT SHOT")
#    cmds.showWindow(win)
#    cmds.columnLayout()
#
#    cmds.rowLayout(nc=3)
#    self.prefix = cmds.textFieldGrp('search_field')
#    cmds.button(label="Search", c=lambda x: self.search())
#    cmds.button(label="X", c=lambda x: self.base_list())
#    cmds.setParent('..')
#
#    selection = cmds.textScrollList( "Shot_List", numberOfRows=8,
#                    append=self.shot_list,
#                    selectIndexedItem=1, showIndexedItem=1)
#
#    cmds.rowLayout(numberOfColumns=2)
#    cmds.button(label="Select Current Shot", c=lambda x: self.select_current_shot(selection))
#    cmds.button(label="Next", c=lambda x: self.save_shot(self.getSelected(selection)[0]))
#    cmds.setParent("..")
#
# Supports the Shot select gui by implementing a search function
# def search(self):
#    searchEntry = cmds.textFieldGrp('search_field', q=True, text=True)
#    cmds.textScrollList( "Shot_List", edit=True, removeAll=True)
#
#    tempList = []
#    for element in self.shot_list:
#        if searchEntry.lower() in element.lower():
#            tempList.append(element)
#    cmds.textScrollList( "Shot_List", edit=True, append=tempList)
#
# Supports the Shot selection by clearing the search function and returning to the base list
# def base_list(self):
#    cmds.textScrollList( "Shot_List", edit=True, removeAll=True)
#    cmds.textScrollList( "Shot_List", edit=True, append=self.shot_list)
#    cmds.textFieldGrp('search_field', edit=True, text="")
#
# Selects from the list displayed in the shot selection gui, the shot item correlation to the current maya file
# def select_current_shot(self, scrollList):
#
#    fullNamePath = cmds.file( q =1, sn = 1)
#    dirPath = os.path.dirname(fullNamePath)
#    shotName = dirPath.split('/')[-1]
#    print(fullNamePath, dirPath, shotName)
#
#    if shotName in self.shot_list:
#        #Sets the selection to the currently opened shot
#        cmds.textScrollList( scrollList, edit=True, selectItem=shotName)
#    else:
#        confirm = cmds.confirmDialog ( title='WARNING', message="The current Maya file is not in the shot list", button=['Ok'], defaultButton='Ok', dismissString='Other' )
#        if confirm == "Ok":
#            pass
#
# Gets object name, changes spaces to underscores if any
# def object_name_results(self):
#    self.object_selection = cmds.textFieldGrp('comment', q=True, text=True)
#    self.object_selection = self.object_selection.replace(" ", "_")
#
#    if cmds.window('msOtherObjWindowID', exists=True):
#        cmds.deleteUI('msOtherObjWindowID')
#
#    self.shot_select_gui()
#
#    #Generates the file path where the alembic will be stored. If there is an alembic there already, versions
#    #   if not, it creates a base version and an .element file and an object_main.abc
# def exporter(self):
#
#    asset = pipe.server.get_asset(self.object_selection)
#    shot = pipe.server.get_shot(self.shot_selection)
#
#    anim_filepath = shot.path + '/anim'
#    if not self.dir_exists(anim_filepath):
#        os.mkdir(self.anim_filepath)
#
#    self.usd_filepath = anim_filepath + '/' + asset.name.lower() + '/' + asset.name.lower() + '.usd'
#    print(self.usd_filepath)
#
#    command = self.get_alembic_command()
#
#    self.version_alembic(command)
#    self.version_usd()
#    #self.comment_gui()
#
# Checks if a dir exists, returns True or False
# def dir_exists(self, dir_path):
#    my_file = Path(dir_path)
#    return my_file.is_dir()
#
# Checks if the given directory is empty, returns True or False
# def dir_isEmpty(self, dir_path):
#    dir_list = os.listdir(dir_path)
#
#    if len(dir_list) == 0:
#        return True
#    else:
#        return False
#
# Gets the commands needed for an alembic export. Updates the alem_filepath to match
# def get_alembic_command(self):
#    start = self.startFrame
#    end = self.endFrame
#    root = ""
#    curr_selection = cmds.ls(selection=True)
#    for obj in curr_selection:
#        if root != "":
#            root = root + " "
#        root = root + "-root " + obj
#
#    tmp = os.getenv('TMPDIR')
#    save_name = tmp + "/" + self.object_selection.lower() + ".abc"
#
#    self.alem_filepath = save_name
#
#    command = "-frameRange " + start + " " + end + " -uvWrite -worldSpace -stripNamespaces " + root + " -file " + save_name
#    print("command: " + command)
#    return command
#
# Exports and versions the alembic
# def version_alembic(self, command):
#    #Export alembic to $TEMP_DIR
#    cmds.AbcExport( j=command)
#
#
#    #Get new version number
#    #self.ver_num = self.el.get_latest_version() + 1
#    #dir_name = ".v" + f"{self.ver_num:04}"
#    #Make hidden directory with version number
#    #new_dir_path = os.path.join(self.curr_env.get_file_dir(self.el.filepath), dir_name)
#    #os.mkdir(new_dir_path)
#    #Copy alembic into the new directory and rename it
#    #new_file_path = new_dir_path + "/" + self.el.get_file_parent_name() + self.el.get_file_extension()
#    #shutil.copy(self.el.filepath, new_file_path)
#
#    # Set permissions
#    #permissions.set_permissions(self.el.filepath)
#    #permissions.set_permissions(new_file_path)
#
# Finds the alembic in the temp folder, converts to usd and saves in pipe
# def version_usd(self):
#    file_path = self.alem_filepath
#    output_file = self.usd_filepath
#
#    usd_data = Sdf.Layer.FindOrOpen(file_path)
#    usd_data.Export(output_file)
#
# updates the element file with the comment
# def update_element_file(self):
#    #Adds new publish log to list of publishes
#    self.comment = "v" + str(self.ver_num) + ": " + self.comment
#    self.el.add_publish_log(self.comment)
#    #Set latest version
#    self.el.set_latest_version(self.ver_num)
#    #Write the .element file to disk
#    self.el.write_element_file()
#
#
# def comment_gui(self):
#    #Make list of past comments for the gui
#    publishes = self.el.get_publishes_list()
#    if len(publishes) > 10:
#        publishes = publishes[-10:]
#    publishes_list = []
#    if len(publishes) != 0:
#        for publish in publishes:
#            label = publish[0] + ' ' + publish[1] + ' ' + publish[2] + '\n'
#            publishes_list.insert(0, label)
#
#    # Make a new default window
#    windowID = 'msCommentWindowID'
#
#    if cmds.window(windowID, exists=True):
#        cmds.deleteUI(windowID)
#
#    self.window = cmds.window(windowID, title="Comment", sizeable=False, iconName='Short Name',
#                                resizeToFitChildren=True)
#
#    cmds.rowColumnLayout(nr=5)
#
#    cmds.textScrollList( "Publish_List", numberOfRows=8, append=publishes_list)
#
#    # Comment box
#    cmds.rowLayout(nc=1)
#    self.prefix = cmds.textFieldGrp('comment', label='Comment:')
#    cmds.setParent('..')
#
#
#    # Create export button
#    cmds.columnLayout(adjustableColumn=True, columnAlign='center')
#    cmds.button(label='Export', command=lambda x: self.comment_results())
#    cmds.setParent('..')
#    cmds.showWindow(self.window)
#
# Gets comment, versions the file and updates the .element file
# def comment_results(self):
#    self.comment = cmds.textFieldGrp('comment', q=True, text=True)
#    self.update_element_file()
#
#    if cmds.window('msCommentWindowID', exists=True):
#        cmds.deleteUI('msCommentWindowID')
#
# Inputs the current playback range frames into the FrameRangeWindow text fields
# def select_playback_range(self):
#    start_frame = cmds.playbackOptions(q=True, min=True)
#    end_frame = cmds.playbackOptions(q=True, max=True)
#
#    cmds.textFieldGrp('startFrame', edit=True, text=int(start_frame))
#    cmds.textFieldGrp('endFrame', edit=True, text=int(end_frame))
#
# GUI: Prompts for the first and last frame to export
# def get_frameRange_gui(self):
#    # Make a new default window
#    windowID = 'msFrameRangeWindowID'
#    if cmds.window(windowID, exists=True):
#        cmds.deleteUI(windowID)
#
#    self.window = cmds.window(windowID, title="Select Frame Range", sizeable=False, iconName='Short Name',
#                                resizeToFitChildren=True)
#
#    cmds.rowColumnLayout(nr=5)
#
#    # StartFrame and EndFram boxes
#    cmds.rowLayout(nc=4)
#    cmds.textFieldGrp('startFrame', label='Start Frame:')
#    cmds.textFieldGrp('endFrame', label='End Frame:')
#    cmds.setParent('..')
#    cmds.separator(h=30, vis=True)
#
#    # Create a Playback range button
#    cmds.rowLayout(nc=2)
#    cmds.button(label='PlayBack range', command=lambda x: self.select_playback_range())
#    cmds.button(label='Export', command=lambda x: self.get_frameRange())
#    cmds.setParent('..')
#    cmds.showWindow(self.window)
#
# Saves the frame range from the gui, then triggers the exporter
# def get_frameRange(self):
#
#    self.startFrame = cmds.textFieldGrp('startFrame', q=True, text=True)
#    self.endFrame = cmds.textFieldGrp('endFrame', q=True, text=True)
#
#
#
#    error_message = ""
#    if not self.startFrame or not self.endFrame:
#        error_message = "Entries can not be empty"
#    elif not self.startFrame.isdigit():
#        if self.startFrame[0] == '-' and self.startFrame[1:].isdigit():
#            pass
#        else:
#            error_message = "Entries must be integers"
#    elif not self.endFrame.isdigit():
#        if self.endFrame[0] == '-' and self.endFrame[1:].isdigit():
#            pass
#        else:
#            error_message = "Entries must be integers"
#    elif self.endFrame < self.startFrame:
#        error_message = "End frame must be greater than the start frame"
#
#    if error_message != "":
#        confirm = cmds.confirmDialog ( title='WARNING', message=error_message, button=['Ok'], defaultButton='Ok', dismissString='Other' )
#        if confirm == "Ok":
#            pass
#    else:
#        if cmds.window('msFrameRangeWindowID', exists=True):
#            cmds.deleteUI('msFrameRangeWindowID')
#        self.exporter()
