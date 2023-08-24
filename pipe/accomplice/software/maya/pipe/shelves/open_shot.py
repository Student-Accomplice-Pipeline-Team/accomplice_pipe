# import os
# import maya.cmds as cmds
# import pipe 

# def open_shot_file():
#     unsaved_changes = cmds.file(query=True, modified=True)
#     if unsaved_changes:
#         response = cmds.confirmDialog(
#             title="Unsaved Changes",
#             message="The current file has unsaved changes. Continue anyways?",
#             button=["Continue", "Cancel"],
#             defaultButton="Cancel",
#             cancelButton="Cancel",
#             dismissString="Cancel"
#         )
#         if response == "Cancel":
#             return
    
#     shot_names = pipe.server.get_shot_list()
    
#     shot_response = cmds.layoutDialog( # Returns '1' if user clicked 'okay' and '0' otherwise (literally returns a string)
#         ui=lambda: shot_dialog(shot_names),
#         title="Open Shot File"
#     )
    
#     shot_name = None
#     if shot_response == "1":  # User clicked "OK"
#         selected_shot_index = cmds.textScrollList(shot_list, query=True, selectIndexedItem=True)[0] - 1
#         if selected_shot_index >= 0:
#             shot_name = shot_names[selected_shot_index]
#             # Now you can use the selected shot name for further processing
#     else:
#         print("User canceled shot selection")

#     print(shot_name) # TODO: Fix this! :)
#     shot = pipe.server.get_shot(shot_name)
    
#     # subfile_types = ['main', 'anim', 'camera', 'fx', 'layout', 'lighting']

#     file_path = shot.get_shotfile()
    
#     if os.path.isfile(file_path):
#         cmds.file(file_path, open=True, force=True)
#     else:
#         cmds.file(new=True, force=True)
#         cmds.file(rename=file_path)
#         cmds.file(save=True)
#         cmds.file(save=True)

# def shot_dialog(shot_names):
#     result = cmds.columnLayout(adjustableColumn=True)
#     cmds.text(label="Select the Shot File that you'd like to open.")
#     shot_list = cmds.textScrollList(numberOfRows=4, allowMultiSelection=False)
#     for shot_name in shot_names:
#         cmds.textScrollList(shot_list, edit=True, append=shot_name)
#     cmds.button(label="OK", command=lambda _: cmds.layoutDialog(dismiss="1"))
#     cmds.button(label="Cancel", command=lambda _: cmds.layoutDialog(dismiss="0"))
#     cmds.setParent("..")
#     return result

# open_shot_file()

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
