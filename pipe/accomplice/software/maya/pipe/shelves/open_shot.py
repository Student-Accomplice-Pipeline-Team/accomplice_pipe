import os
import maya.cmds as cmds
import pipe
from PySide2 import QtWidgets, QtGui, QtCore

class ShotFileDialog(QtWidgets.QDialog):
    """ A PyQt class for holding the list of shot files """
    def __init__(self, shot_names, parent=None):
        super(ShotFileDialog, self).__init__(parent)
        self.setWindowTitle("Open Shot File")
        
        layout = QtWidgets.QVBoxLayout()
        
        self.shot_list = QtWidgets.QListWidget()
        layout.addWidget(self.shot_list)
        
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        for shot_name in shot_names:
            item = QtWidgets.QListWidgetItem(shot_name)
            self.shot_list.addItem(item)
        
        self.setLayout(layout)

def open_file(file_path):
    """ Opens a new Maya file """
    cmds.file(file_path, open=True, force=True)

def create_new_file(file_path):
    """ Creates a new Maya file """
    cmds.file(new=True, force=True)
    cmds.file(rename=file_path)
    cmds.file(save=True)
    
def create_maya_file_path_from_houdini_shot_file(houdini_file_path: str):
    """ A really hacky thing that needs to be deleted that creates what might be the path to the maya version of this file """
    assert houdini_file_path.endswith(".hipnc")
    return houdini_file_path.replace(".hipnc", ".mb") # Switch out the file extension :)

def open_shot_file():
    unsaved_changes = cmds.file(query=True, modified=True)
    if unsaved_changes:
        response = cmds.confirmDialog(
            title="Unsaved Changes",
            message="The current file has unsaved changes. Continue anyway?",
            button=["Continue", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel",
            dismissString="Cancel"
        )
        if response == "Cancel":
            return
    
    shot_names = pipe.server.get_shot_list()
    
    shot_dialog = ShotFileDialog(shot_names)
    result = shot_dialog.exec_()
    
    if result == QtWidgets.QDialog.Accepted:
        selected_item = shot_dialog.shot_list.currentItem()
        if selected_item:
            shot_name = selected_item.text()
            shot = pipe.server.get_shot(shot_name)
            
            file_path = shot.get_shotfile(type='anim')
            file_path = create_maya_file_path_from_houdini_shot_file(file_path) # TODO: This is scary, fix this! :)
            print(file_path)
            
            if os.path.isfile(file_path): # If the file exists
                # Open the file
                open_file(file_path)
            else: # Otherwise, open a new tile and save it
                create_new_file(file_path)

open_shot_file()