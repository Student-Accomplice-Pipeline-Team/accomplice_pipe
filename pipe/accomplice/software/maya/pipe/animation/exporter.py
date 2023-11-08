import maya.cmds as cmds
import pymel.core as pm
from pathlib import Path
import os, shutil
import pipe.shared.permissions as p
from pipe.shared.helper.utilities.file_path_utils import FilePathUtils
import maya.mel as mel

import pipe
from pxr import Sdf

"""from pipe.tools.maya.UnMaya_PipeHandlers import unMaya_Element as umEl
from pipe.tools.maya.UnMaya_PipeHandlers import unMaya_Environment as umEnv
import pipe.pipeHandlers.permissions as permissions
import pipe.config as config"""

# TODO: Get frame range from shotgrid


class Exporter:
    def __init__(self):
        self.ANIM_DIR = "anim"
        self.ALEMBIC_EXPORTER_SUFFIX = ":EXPORTSET_Alembic"
        self.FBX_EXPORTER_SUFFIX = ":EXPORTSET_CarLocWS"
        self.CAR_FBX_NAME = "world_space_car_transform.fbx"

    def run(self):
        print("Alembic Exporter not ready yet")

        # self.check_if_selected() # I commented this out so that ideally the script selects the object automatically
        self.object_select_gui()

    def check_if_selected(self):
        curr_selection = cmds.ls(selection=True)
        if len(curr_selection) == 0:
            confirm = cmds.confirmDialog(
                title="WARNING",
                message="Nothing is selected",
                button=["Ok"],
                defaultButton="Ok",
                dismissString="Other",
            )
            if confirm == "Ok":
                pass
        else:
            self.object_select_gui()

    # Receives a textScrollList and returns the currently selected list item
    def getSelected(self, scrollList):
        selected = cmds.textScrollList(scrollList, q=1, si=1)
        return selected

    # This is a GUI that presents four options of what you are exporting. The one selected will determine the location that the object is created in
    def object_select_gui(self):
        object_list = ["letty", "vaughn", "ed", "studentcar", "other"]

        if cmds.window("ms_selectObject_GUI", exists=True):
            cmds.deleteUI("ms_selectObject_GUI")

        win = cmds.window("ms_selectObject_GUI", title="SELECT OBJECT GUI")
        cmds.showWindow(win)
        cmds.columnLayout()

        selection = cmds.textScrollList(
            "Object_List",
            numberOfRows=8,
            append=object_list,
            selectIndexedItem=1,
            showIndexedItem=1,
        )

        cmds.rowLayout(numberOfColumns=1)

        # selected_name =

        cmds.button(
            label="Next", c=lambda x: self.save_object(self.getSelected(selection)[0])
        )
        cmds.setParent("..")

    # Stores the selected object in a variable to be used later. Triggers a text prompt if "other" was selected. Else triggers the Shot select gui
    def save_object(self, selected_object):
        # Delete Object Select GUI
        if cmds.window("ms_selectObject_GUI", exists=True):
            cmds.deleteUI("ms_selectObject_GUI")

        self.object_selection = selected_object

        if self.object_selection == "other":
            self.other_object_gui()
        else:
            # Select the object in the scene for alembic exporting
            # Because there is a descrepancy between the name of the car in the pipeline (studentcar) and the name of the rig (heroCar), we hard code the selection here
            if self.object_selection == "studentcar":
                cmds.select("heroCar" + self.ALEMBIC_EXPORTER_SUFFIX, replace=True)
            else:
                cmds.select(
                    self.object_selection + self.ALEMBIC_EXPORTER_SUFFIX, replace=True
                )
            # If we can determine the shot name from the current maya file, then we can skip the shot selection GUI
            try:
                shot_name = FilePathUtils.get_shot_name_from_file_path(
                    cmds.file(q=True, sn=True)
                )
            except AssertionError:
                self.shot_select_gui()

            if shot_name is None:
                self.shot_select_gui()
            else:
                self.save_shot(shot_name)

    # Stores the selected shot in a variable to be used later and triggers the framerange gui
    def save_shot(self, selected_shot):
        self.shot_selection = selected_shot
        self.get_frameRange_gui()

        if cmds.window("ms_selectShot_GUI", exists=True):
            cmds.deleteUI("ms_selectShot_GUI")

        # self.exporter()

    # This GUI shows a list of the shots to select
    def shot_select_gui(self):
        self.shot_list = pipe.server.get_shot_list()
        self.shot_list = sorted(self.shot_list)

        if cmds.window("ms_selectShot_GUI", exists=True):
            cmds.deleteUI("ms_selectShot_GUI")

        win = cmds.window("ms_selectShot_GUI", title="SELECT SHOT")
        cmds.showWindow(win)
        cmds.columnLayout()

        cmds.rowLayout(nc=3)
        self.prefix = cmds.textFieldGrp("search_field")
        cmds.button(label="Search", c=lambda x: self.search())
        cmds.button(label="X", c=lambda x: self.base_list())
        cmds.setParent("..")

        selection = cmds.textScrollList(
            "Shot_List",
            numberOfRows=8,
            append=self.shot_list,
            selectIndexedItem=1,
            showIndexedItem=1,
        )

        cmds.rowLayout(numberOfColumns=2)
        # cmds.button(label="Select Current Shot", c=lambda x: self.select_current_shot(selection))
        cmds.button(
            label="Next", c=lambda x: self.save_shot(self.getSelected(selection)[0])
        )
        cmds.setParent("..")

    # Supports the Shot select gui by implementing a search function
    def search(self):
        searchEntry = cmds.textFieldGrp("search_field", q=True, text=True)
        cmds.textScrollList("Shot_List", edit=True, removeAll=True)

        tempList = []
        for element in self.shot_list:
            if searchEntry.lower() in element.lower():
                tempList.append(element)
        cmds.textScrollList("Shot_List", edit=True, append=tempList)

    # Supports the Shot selection by clearing the search function and returning to the base list
    def base_list(self):
        cmds.textScrollList("Shot_List", edit=True, removeAll=True)
        cmds.textScrollList("Shot_List", edit=True, append=self.shot_list)
        cmds.textFieldGrp("search_field", edit=True, text="")

    # Selects from the list displayed in the shot selection gui, the shot item correlation to the current maya file
    def select_current_shot(self, scrollList):
        fullNamePath = cmds.file(q=1, sn=1)
        dirPath = os.path.dirname(fullNamePath)
        shotName = dirPath.split("/")[-1]
        print(fullNamePath, dirPath, shotName)

        if shotName in self.shot_list:
            # Sets the selection to the currently opened shot
            cmds.textScrollList(scrollList, edit=True, selectItem=shotName)
        else:
            confirm = cmds.confirmDialog(
                title="WARNING",
                message="The current Maya file is not in the shot list",
                button=["Ok"],
                defaultButton="Ok",
                dismissString="Other",
            )
            if confirm == "Ok":
                pass

    # Prompts user to enter the name of the object
    def other_object_gui(self):
        windowID = "msOtherObjWindowID"

        if cmds.window(windowID, exists=True):
            cmds.deleteUI(windowID)

        self.window = cmds.window(
            windowID,
            title="Other Object",
            sizeable=False,
            iconName="Short Name",
            resizeToFitChildren=True,
        )

        cmds.rowColumnLayout(nr=5)

        cmds.columnLayout(adjustableColumn=True)
        cmds.text(
            label="Enter the name of the object which alembics are being saved (No spaces)"
        )

        # text box
        cmds.rowLayout(nc=1)
        self.prefix = cmds.textFieldGrp("comment", label="Object Name:")
        cmds.setParent("..")

        # Create export button
        cmds.columnLayout(adjustableColumn=True, columnAlign="center")
        cmds.button(label="Save", command=lambda x: self.object_name_results())
        cmds.setParent("..")
        cmds.showWindow(self.window)

    # Gets object name, changes spaces to underscores if any
    def object_name_results(self):
        self.object_selection = cmds.textFieldGrp("comment", q=True, text=True)
        self.object_selection = self.object_selection.replace(" ", "_")

        if cmds.window("msOtherObjWindowID", exists=True):
            cmds.deleteUI("msOtherObjWindowID")

        self.shot_select_gui()

    # Generates the file path where the alembic will be stored. If there is an alembic there already, versions
    #   if not, it creates a base version and an .element file and an object_main.abc
    def exporter(self):
        asset = self.object_selection
        print(asset)
        shot = pipe.server.get_shot(self.shot_selection)

        # File path for exporting alembics for CFX
        cfx_filepath = shot.path + "/cfx"
        if not self.dir_exists(cfx_filepath):
            os.mkdir(cfx_filepath)
            p.set_RWE(cfx_filepath)

        self.alem_filepath = cfx_filepath + "/" + self.object_selection.lower() + ".abc"

        # File path for exporting wrapped alembics from ANIM
        anim_filepath = shot.path + "/anim"
        if not self.dir_exists(anim_filepath):
            os.mkdir(anim_filepath)
            p.set_RWE(anim_filepath)

        self.usd_filepath = anim_filepath + "/" + asset + "/" + asset + ".usd"
        print(self.usd_filepath)

        command = self.get_alembic_command()

        self.version_alembic(command)
        self.version_usd()

    def dir_exists(self, dir_path) -> bool:
        """Checks if the given directory exists, returns True or False"""
        my_file = Path(dir_path)
        return my_file.is_dir()

    def dir_isEmpty(self, dir_path) -> bool:
        """Checks if the given directory is empty, returns True or False"""

        dir_list = os.listdir(dir_path)

        if len(dir_list) == 0:
            return True
        else:
            return False

    def get_alembic_command(self):
        """Gets the command needed to export the alembic. Updates the alem_filepath to match"""

        start = self.startFrame
        end = self.endFrame
        root = ""
        curr_selection = cmds.ls(selection=True)
        for obj in curr_selection:
            if root != "":
                root = root + " "
            root = root + "-root " + obj

        command = (
            "-frameRange "
            + start
            + " "
            + end
            + " -attr shop_materialpath"
            + " -uvWrite -worldSpace -stripNamespaces "
            + root
            + " -file "
            + self.alem_filepath
        )
        print("command: " + command)
        return command

    def version_alembic(self, command):
        """Exports the alembic and versions it"""
        # Export alembic to $TEMP_DIR
        cmds.AbcExport(j=command)

        # Get new version number
        # self.ver_num = self.el.get_latest_version() + 1
        # dir_name = ".v" + f"{self.ver_num:04}"
        # Make hidden directory with version number
        # new_dir_path = os.path.join(self.curr_env.get_file_dir(self.el.filepath), dir_name)
        # os.mkdir(new_dir_path)
        # Copy alembic into the new directory and rename it
        # new_file_path = new_dir_path + "/" + self.el.get_file_parent_name() + self.el.get_file_extension()
        # shutil.copy(self.el.filepath, new_file_path)

        # Set permissions
        # permissions.set_permissions(self.el.filepath)
        # permissions.set_permissions(new_file_path)

    # Finds the alembic in the temp folder, converts to usd and saves in pipe
    def version_usd(self):
        file_path = self.alem_filepath
        output_file = self.usd_filepath

        usd_data = Sdf.Layer.FindOrOpen(file_path)
        usd_data.Export(output_file)

    def update_element_file(self):
        """Updates the element file with the comment and latest version"""
        # Adds new publish log to list of publishes
        self.comment = "v" + str(self.ver_num) + ": " + self.comment
        self.el.add_publish_log(self.comment)

        # Set latest version
        self.el.set_latest_version(self.ver_num)

        # Write the .element file to disk
        self.el.write_element_file()

    def comment_gui(self):
        """Make list of past comments for the gui"""
        publishes = self.el.get_publishes_list()
        if len(publishes) > 10:
            publishes = publishes[-10:]
        publishes_list = []
        if len(publishes) != 0:
            for publish in publishes:
                label = publish[0] + " " + publish[1] + " " + publish[2] + "\n"
                publishes_list.insert(0, label)

        # Make a new default window
        windowID = "msCommentWindowID"

        if cmds.window(windowID, exists=True):
            cmds.deleteUI(windowID)

        self.window = cmds.window(
            windowID,
            title="Comment",
            sizeable=False,
            iconName="Short Name",
            resizeToFitChildren=True,
        )

        cmds.rowColumnLayout(nr=5)

        cmds.textScrollList("Publish_List", numberOfRows=8, append=publishes_list)

        # Comment box
        cmds.rowLayout(nc=1)
        self.prefix = cmds.textFieldGrp("comment", label="Comment:")
        cmds.setParent("..")

        # Create export button
        cmds.columnLayout(adjustableColumn=True, columnAlign="center")
        cmds.button(label="Export", command=lambda x: self.comment_results())
        cmds.setParent("..")
        cmds.showWindow(self.window)

    # Gets comment, versions the file and updates the .element file
    def comment_results(self):
        self.comment = cmds.textFieldGrp("comment", q=True, text=True)
        self.update_element_file()

        if cmds.window("msCommentWindowID", exists=True):
            cmds.deleteUI("msCommentWindowID")

    # Inputs the current playback range frames into the FrameRangeWindow text fields
    def select_playback_range(self):
        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        cmds.textFieldGrp("startFrame", edit=True, text=int(start_frame))
        cmds.textFieldGrp("endFrame", edit=True, text=int(end_frame))

    # GUI: Prompts for the first and last frame to export
    def get_frameRange_gui(self):
        # Make a new default window
        windowID = "msFrameRangeWindowID"
        if cmds.window(windowID, exists=True):
            cmds.deleteUI(windowID)

        self.window = cmds.window(
            windowID,
            title="Select Frame Range",
            sizeable=False,
            iconName="Short Name",
            resizeToFitChildren=True,
        )

        cmds.rowColumnLayout(nr=5)

        # StartFrame and EndFram boxes
        cmds.rowLayout(nc=4)
        cmds.textFieldGrp("startFrame", label="Start Frame:")
        cmds.textFieldGrp("endFrame", label="End Frame:")
        cmds.setParent("..")
        cmds.separator(h=30, vis=True)

        # Create a Playback range button
        cmds.rowLayout(nc=2)
        cmds.button(
            label="PlayBack range", command=lambda x: self.select_playback_range()
        )
        cmds.button(label="Export", command=lambda x: self.get_frameRange())
        cmds.setParent("..")
        cmds.showWindow(self.window)

    # Saves the frame range from the gui, then triggers the exporter
    def get_frameRange(self):
        self.startFrame = cmds.textFieldGrp("startFrame", q=True, text=True)
        self.endFrame = cmds.textFieldGrp("endFrame", q=True, text=True)

        error_message = ""
        if not self.startFrame or not self.endFrame:
            error_message = "Entries can not be empty"
        elif not self.startFrame.isdigit():
            if self.startFrame[0] == "-" and self.startFrame[1:].isdigit():
                pass
            else:
                error_message = "Entries must be integers"
        elif not self.endFrame.isdigit():
            if self.endFrame[0] == "-" and self.endFrame[1:].isdigit():
                pass
            else:
                error_message = "Entries must be integers"
        elif int(self.endFrame) < int(self.startFrame):
            error_message = "End frame must be greater than the start frame"

        if error_message != "":
            confirm = cmds.confirmDialog(
                title="WARNING",
                message=error_message,
                button=["Ok"],
                defaultButton="Ok",
                dismissString="Other",
            )
            if confirm == "Ok":
                pass
        else:
            if cmds.window("msFrameRangeWindowID", exists=True):
                cmds.deleteUI("msFrameRangeWindowID")
            self.exporter()
