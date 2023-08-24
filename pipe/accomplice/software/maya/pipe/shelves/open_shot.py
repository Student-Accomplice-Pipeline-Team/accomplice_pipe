import os
import maya.cmds as cmds
import pipe
from PySide2 import QtWidgets, QtGui, QtCore

class ShotFileDialog(QtWidgets.QDialog):
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

def open_shot_file():
    unsaved_changes = cmds.file(query=True, modified=True)
    if unsaved_changes:
        response = cmds.confirmDialog(
            title="Unsaved Changes",
            message="The current file has unsaved changes. Continue anyways?",
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
    print("Result: ", result)
    
    if result == QtWidgets.QDialog.Accepted:
        selected_item = shot_dialog.shot_list.currentItem()
        print("Selected Item: ", selected_item.text())
        if selected_item:
            shot_name = selected_item.text()
            shot = pipe.server.get_shot(shot_name)
            
            file_path = shot.get_shotfile()
            
            if os.path.isfile(file_path):
                cmds.file(file_path, open=True, force=True)
            else:
                cmds.file(new=True, force=True)
                cmds.file(rename=file_path)
                cmds.file(save=True)
                cmds.file(save=True)

open_shot_file()
