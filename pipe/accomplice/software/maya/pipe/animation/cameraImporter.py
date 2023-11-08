import pipe
import pipe.shared.versions as vs

import maya.cmds as cmds
import maya.mel as mel
from pathlib import Path
from re import match
import os
import shutil


class CameraImporter:
    def __init__(self):
        print("Starting...")

    def run(self):
        print("About to import Camera...")

        self.shot_select_gui()

    # Receives a textScrollList and returns the currently selected list item
    def getSelected(self, scrollList):
        selected = cmds.textScrollList(scrollList, q=1, si=1)
        return selected

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
            label="Import", c=lambda x: self.save_shot(self.getSelected(selection)[0])
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
        self.shot_selection = pipe.server.get_shot(selected_shot)
        self.import_camera()

        if cmds.window("ms_selectShot_GUI", exists=True):
            cmds.deleteUI("ms_selectShot_GUI")

    def import_camera(self):
        camera_path = self.shot_selection.get_camera("RLO")

        if not camera_path:
            confirm = cmds.confirmDialog(
                title="WARNING",
                message="No camera has been exported for this shot",
                button=["Ok"],
                defaultButton="Ok",
                dismissString="Other",
            )
            if confirm == "Ok":
                return

        cam_nodes = cmds.file(
            camera_path,
            type="USD Import",
            options=";shadingMode=[[useRegistry,rendermanForMaya],[useRegistry,MaterialX],[pxrRis,none],[useRegistry,UsdPreviewSurface],[displayColor,none],[none,none]];preferredMaterial=none;primPath=/;readAnimData=1;useCustomFrameRange=0;startTime=0;endTime=0;importUSDZTextures=0",
            importFrameRate=True,
            importTimeRange="override",
            i=True,
            returnNewNodes=True,
        )

        cam = list(filter(lambda v: match("^[^|]*\|[^|]*$", v), cam_nodes))
        cmds.rename(cam, self.shot_selection.name + "_CAM")

        # mel.eval('file -import -type "USD Import"  -ignoreVersion -ra true -mergeNamespacesOnClash false -namespace "camera_A_030__F1_111_" -options ";shadingMode=[[useRegistry,rendermanForMaya],[useRegistry,MaterialX],[pxrRis,none],[useRegistry,UsdPreviewSurface],[displayColor,none],[none,none]];preferredMaterial=none;primPath=/;readAnimData=1;useCustomFrameRange=0;startTime=0;endTime=0;importUSDZTextures=0"  -pr  -importFrameRate true  -importTimeRange "override" "' + camera_path + '";')
