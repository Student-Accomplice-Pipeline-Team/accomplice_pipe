def convert_to_single_line_command_string(string):
    content = string
    single_line = content.replace('\n', '\\n').replace('"', '\\"')
    return f'-command "{single_line}"'

def convert_to_single_line_command(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return convert_to_single_line_command_string(content)
    except FileNotFoundError:
        return "File not found."

def test_full_conversion():
    full_test_script = """
import os
import maya.cmds as cmds
import pipe
from PySide2 import QtWidgets, QtGui, QtCore

class ShotFileDialog(QtWidgets.QDialog):
    \"\"\" A PyQt class for holding the list of shot files \"\"\"
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

class InfoDialog(QtWidgets.QDialog):
    def __init__(self, dialog_title, dialog_message, include_cancel_button = False, parent=None):
        super(InfoDialog, self).__init__(parent)
        self.setWindowTitle(dialog_title)
        
        layout = QtWidgets.QVBoxLayout()

        message_label = QtWidgets.QLabel(dialog_message)  # Create a label for the message
        layout.addWidget(message_label)  # Add the label to the layout

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        if include_cancel_button:
            cancel_button = QtWidgets.QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            layout.addWidget(cancel_button)

        self.setLayout(layout)


def open_file(file_path):
    \"\"\" Opens a new Maya file \"\"\"
    cmds.file(file_path, open=True, force=True)

def create_new_file(file_path:str, shot):
    \"\"\" Creates a new Maya file \"\"\"
    directory = os.path.dirname(file_path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    cmds.file(new=True, force=True)
    cmds.file(rename=file_path)
    set_frame_range(shot)
    cmds.file(save=True)
    
def set_frame_range(shot, global_start_frame=1001, handle_frames=5):
    handle_start, shot_start, shot_end, handle_end = shot.get_shot_frames(global_start_frame=global_start_frame, handle_frames=handle_frames)
    cmds.playbackOptions(animationStartTime=handle_start, animationEndTime=handle_end)
    cmds.playbackOptions(minTime=shot_start, maxTime=shot_end)

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
    
    shot_names = sorted(pipe.server.get_shot_list())
    
    shot_dialog = ShotFileDialog(shot_names)
    result = shot_dialog.exec_()
    
    if result == QtWidgets.QDialog.Accepted:
        selected_item = shot_dialog.shot_list.currentItem()
        if selected_item:
            shot_name = selected_item.text()
            shot = pipe.server.get_shot(shot_name, retrieve_from_shotgrid=True)
            
            file_path = shot.get_maya_shotfile_path()
            
            if os.path.isfile(file_path): # If the file exists
                # Open the file
                open_file(file_path)
            else: # Otherwise, open a new tile and save it
                dialog = InfoDialog("Create New File", "Shot " + shot_name + " does not yet exist. Would you like to create it?", include_cancel_button=True)
                response = dialog.exec_()
                if response == QtWidgets.QDialog.Accepted:
                    create_new_file(file_path, shot)
                else:
                    dialog = InfoDialog("Shot not created.", "The shot was not created.")
                    response = dialog.exec_()
                    

open_shot_file()
"""

    # Create a temporary file path
    full_test_file_path = '/tmp/full_test_script.py'

    # Write the full test script to the file
    with open(full_test_file_path, 'w') as full_test_file:
        full_test_file.write(full_test_script)

    # Perform the conversion
    result = convert_to_single_line_command(full_test_file_path)

    # Return the result
    return result

# Test the conversion with the full script
test_full_conversion_result = test_full_conversion()
print(test_full_conversion_result)