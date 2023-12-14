import maya.cmds as cmds
import os
import pathlib
from pipe.shared.versions import VersionManager
import time
from PySide2 import QtWidgets
import pipe
from pipe.shared.helper.utilities.ui_utils import ListWithFilter, InfoDialog

class MayaFileManager:
    def __init__(self):
        current_file_path = cmds.file(query=True, sceneName=True)
        if not current_file_path:
            QtWidgets.QMessageBox.warning(None, 'No File Open', 'No file is currently open. Open a file and try again.')
            raise Exception("No file is currently open. Open a file and try again.")
        self.vm = VersionManager(current_file_path)

    def save_new_version(self):
        if MayaFileManager.check_for_unsaved_changes_and_inform_user():
            return

        self.vm.save_new_version()
        QtWidgets.QMessageBox.information(None, 'Version Saved', 'A new version has been saved.')

    def show_current_version(self):
        current_version = self.vm.get_current_version_number()
        QtWidgets.QMessageBox.information(None, 'Current Version', f'The current version is {current_version}.')

    def switch_version_ui(self):
        version_table = self.vm.get_version_table()

        # Sort the version table by timestamp
        version_table_sorted = sorted(version_table, key=lambda x: x[2])

        current_version_number = self.vm.get_current_version_number()

        if hasattr(self, 'versionSwitchWindow') and self.versionSwitchWindow:
            self.versionSwitchWindow.close()

        self.versionSwitchWindow = QtWidgets.QWidget()
        self.versionSwitchWindow.setWindowTitle("Switch to Version (Current Version: " + str(current_version_number) + ")")
        layout = QtWidgets.QVBoxLayout(self.versionSwitchWindow)

        for file, version_number, timestamp, note in version_table_sorted:
            timestamp_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            btn = QtWidgets.QPushButton(f"Version {version_number} - {timestamp_readable} - Note: {note}")
            btn.clicked.connect(lambda checked=False, vn=version_number: self.switch_to_selected_version(vn))
            layout.addWidget(btn)

        self.versionSwitchWindow.show()

    def switch_to_selected_version(self, version_number):
        if MayaFileManager.check_for_unsaved_changes_and_inform_user():
            return

        if hasattr(self, 'versionSwitchWindow') and self.versionSwitchWindow:
            self.versionSwitchWindow.close()

        self.vm.switch_to_version(version_number)

        # Open the file in Maya
        OpenNewFileManager.open_file(self.vm.get_main_path())
        QtWidgets.QMessageBox.information(None, 'Version Switched', f'Switched to version {version_number}.')

    def edit_version_note(self):
        current_version = self.vm.get_current_version_number()
        existing_note = self.vm.get_note_for_version(current_version)

        text, ok = QtWidgets.QInputDialog.getText(None, 'Edit Note', f'Enter Note for Version {current_version}:', text=existing_note)

        if ok:
            new_note = text
            self.vm.set_note_for_version(current_version, new_note)

    @staticmethod
    def check_for_unsaved_changes_and_inform_user():
        if cmds.file(query=True, modified=True):
            result = QtWidgets.QMessageBox.warning(None, 'Unsaved Changes', 'The current file has unsaved changes. Please save before continuing.', QtWidgets.QMessageBox.Ok)
            return True
        return False
    
    @staticmethod
    def get_names_of_all_maya_shots_that_have_been_created(ensure_shots_in_shotgrid=True):
        """
        Returns a list of the names of all Maya shots that have been created.
        """
        import glob
        base_dir = "/groups/accomplice/pipeline/production/sequences" # TODO: Where's a better place to get this from?

        # Pattern to match all Maya files in the specified structure
        pattern = os.path.join(base_dir, "*", "shots", "*", "anim", "*_*.mb")

        # Find all files that match the pattern
        maya_files = list(glob.glob(pattern))

        base_names = sorted([pathlib.Path(f).stem.replace('_anim', '') for f in maya_files])
        if ensure_shots_in_shotgrid:
            all_shot_names = pipe.server.get_shot_list()
            return [base_name for base_name in base_names if base_name in all_shot_names]
        return base_names


class OpenNewFileManager:
    @staticmethod
    def open_file(file_path): # TODO: update this to use the Version Manager!
        """ Opens a new Maya file """
        cmds.file(file_path, open=True, force=True)
        vm = VersionManager(file_path) # This ensures that a symlink version is created if it doesn't already exist.

    @staticmethod
    def create_new_file(file_path:str, shot):
        """ Creates a new Maya file """
        directory = os.path.dirname(file_path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        cmds.file(new=True, force=True)
        cmds.file(rename=file_path)
        OpenNewFileManager.set_frame_range(shot)
        cmds.file(save=True)

        vm = VersionManager(file_path)
        
    @staticmethod
    def set_frame_range(shot, global_start_frame=1001, handle_frames=5):
        handle_start, shot_start, shot_end, handle_end = shot.get_shot_frames(global_start_frame=global_start_frame, handle_frames=handle_frames)
        cmds.playbackOptions(animationStartTime=handle_start, animationEndTime=handle_end)
        cmds.playbackOptions(minTime=shot_start, maxTime=shot_end)

    @staticmethod
    def ask_to_continue_with_unsaved_changes(message="The current file has unsaved changes. Continue anyway?"):
        unsaved_changes = cmds.file(query=True, modified=True)
        if unsaved_changes:
            response = cmds.confirmDialog(
                title="Unsaved Changes",
                message=message,
                button=["Continue", "Cancel"],
                defaultButton="Cancel",
                cancelButton="Cancel",
                dismissString="Cancel"
            )
            if response == "Cancel":
                return False
        return True
    
    @staticmethod
    def open_shot_file():
        unsaved_changes = OpenNewFileManager.ask_to_continue_with_unsaved_changes()
        if not unsaved_changes:
            return
        
        shot_names = sorted(pipe.server.get_shot_list())
        
        shot_dialog = ListWithFilter("Select the Shot to Open", shot_names)
        
        if shot_dialog.exec_() == QtWidgets.QDialog.Accepted:
            shot_name = shot_dialog.get_selected_item()
            if shot_name:
                shot = pipe.server.get_shot(shot_name, retrieve_from_shotgrid=True)
                OpenNewFileManager.open_shot(shot)
                

    @staticmethod
    def open_shot(shot):
        file_path = shot.get_maya_shotfile_path()
        
        if os.path.isfile(file_path): # If the file exists
            # Open the file
            OpenNewFileManager.open_file(file_path)
        else: # Otherwise, open a new tile and save it
            dialog = InfoDialog("Create New File", "Shot " + shot.get_name() + " does not yet exist. Would you like to create it?", include_cancel_button=True)
            response = dialog.exec_()
            if response == QtWidgets.QDialog.Accepted:
                OpenNewFileManager.create_new_file(file_path, shot)
            else:
                dialog = InfoDialog("Shot not created.", "The shot was not created.")
                response = dialog.exec_()
        