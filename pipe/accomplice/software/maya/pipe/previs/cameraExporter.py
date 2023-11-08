import pipe
import pipe.shared.versions as vs

import maya.cmds as cmds
import maya.mel as mel
from pathlib import Path
import os
import shutil


class CameraExporter:
    def __init__(self):
        print("starting i guess...")

    def run(self):
        print("About to export Camera...")

        self.check_if_selected()

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
            self.shot_select_gui()

    # Receives a textScrollList and returns the currently selected list item
    def getSelected(self, scrollList):
        selected = cmds.textScrollList(scrollList, q=1, si=1)
        return selected

    # Inputs the current playback range frames into the FrameRangeWindow text fields
    def select_playback_range(self):
        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        cmds.textFieldGrp("startFrame", edit=True, text=int(start_frame))
        cmds.textFieldGrp("endFrame", edit=True, text=int(end_frame))

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

    # Stores the selected shot in a variable to be used later and triggers the framerange gui

    def save_shot(self, selected_shot):
        self.shot_selection = selected_shot
        self.get_frameRange_gui()

        if cmds.window("ms_selectShot_GUI", exists=True):
            cmds.deleteUI("ms_selectShot_GUI")

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
        elif self.endFrame < self.startFrame:
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

    # Generates the file path where the alembic will be stored. If there is an alembic there already, versions

    def exporter(self):
        shot = pipe.server.get_shot(self.shot_selection)

        self.camera_filepath = os.path.join(shot.path, "camera", "RLO")
        if not os.path.exists(self.camera_filepath):
            os.makedirs(self.camera_filepath)

        # unused
        frameRange = "_F" + str(int(self.startFrame)) + "-" + str(int(self.endFrame))

        self.usd_filepath = os.path.join(
            self.camera_filepath, "camera_" + shot.name + ".usd"
        )
        print(self.usd_filepath)

        self.version_camera_animation()

    def version_camera_animation(self):
        # Do the things to the camera

        origCam = cmds.ls(sl=True)[0]
        camName = origCam.split(":")[0].replace("_", "") + "tmp"

        newCam = cmds.duplicate(origCam, n=camName)[0]
        cmds.select(newCam)
        cmds.parent(w=True)
        cmds.rename(newCam, camName)

        camShape = cmds.listRelatives(newCam, children=True, fullPath=True, s=True)[
            0
        ]  # Get a list of all children
        camChildren = cmds.listRelatives(
            newCam, children=True, fullPath=True
        )  # Get a list of all children

        for child in camChildren:
            if child != camShape:
                cmds.delete(child)  # Delete each child

        cmds.select(newCam)
        self.lockUnlockChannels(lock=False)

        # constrain, bake, clean up

        cmds.parentConstraint(origCam, newCam, mo=0)
        cmds.bakeResults(newCam, t=(self.startFrame, self.endFrame))
        cmds.delete(cn=1)

        version_path = vs.get_next_version(self.usd_filepath)
        try:
            mel.eval(
                'file -force -options ";exportUVs=0;exportSkels=none;exportSkin=none;'
                + "exportBlendShapes=0;exportDisplayColor=0;exportColorSets=0;"
                + "defaultMeshScheme=none;animation=1;eulerFilter=0;staticSingleSample=0;startTime="
                + str(self.startFrame)
                + ";endTime="
                + str(self.endFrame)
                + ";"
                + "frameStride=1;frameSample=0.0;defaultUSDFormat=usdc;parentScope=;"
                + "shadingMode=useRegistry;convertMaterialsTo=[UsdPreviewSurface];exportInstances=1;"
                + 'exportVisibility=1;mergeTransformAndShape=1;stripNamespaces=0" -typ "USD Export" -pr -eur -es "'
                + version_path
                + '"'
            )
            vs.update_symlink(self.usd_filepath, version_path)
        except Exception as e:
            print(e)
            confirm = cmds.confirmDialog(
                title="WARNING",
                message="Export Failed. More info in the console.",
                button=["Ok"],
                defaultButton="Ok",
                dismissString="Other",
            )
            if confirm == "Ok":
                pass

        cmds.select(newCam)
        cmds.delete()

        cmds.confirmDialog(
            title="Export Successful!",
            message="Your camera has been exported to:" + self.usd_filepath,
            button="Ok",
        )

        cmds.select(origCam)

    def lockUnlockChannels(
        self,
        channels=["T", "R", "S"],
        lock="",
        keyable="",
        hide="",
        breakConnections="",
    ):
        sel = cmds.ls(sl=True)

        myChannels = []

        for chan in channels:
            if chan == "T":
                myChannels.extend([".tx", ".ty", ".tz"])
            elif chan == "R":
                myChannels.extend([".rx", ".ry", ".rz"])
            elif chan == "S":
                myChannels.extend([".sx", ".sy", ".sz"])
            elif chan in "tx ty tz rx ry rz sx sy sz":
                myChannels.append("." + chan)

        if hide == True:
            hideVal = False

        if hide == False:
            hideVal = True

        for y in range(len(sel)):
            for x in range(len(myChannels)):
                if lock != "":
                    cmds.setAttr(sel[y] + myChannels[x], lock=lock)
                if keyable != "":
                    cmds.setAttr(
                        sel[y] + myChannels[x], keyable=keyable, channelBox=True
                    )
                if hide != "":
                    cmds.setAttr(sel[y] + myChannels[x], keyable=hideVal)
                if breakConnections == True:
                    con = cmds.listConnections(sel[y] + myChannels[x], s=1, p=1)
                    try:
                        cmds.disconnectAttr(con[0], sel[y] + myChannels[x])
                    except:
                        pass
