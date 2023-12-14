import maya.cmds as cmds
import os
import pathlib
from pipe.shared.versions import VersionManager
from PySide2 import QtWidgets
import pipe
from pipe.shared.helper.utilities.ui_utils import ListWithFilter, InfoDialog
from pipe.shared.helper.utilities.dcc_version_manager import DCCVersionManager

class MayaFileManager:
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
class MayaFileVersionManager(DCCVersionManager):
    def get_my_path(self):
        current_file_path = cmds.file(query=True, sceneName=True)
        return current_file_path

    def open_file(self):
        OpenNewFileManager.open_file(self.vm.get_main_path())

    def check_for_unsaved_changes_and_inform_user(self):
        return MayaFileManager.check_for_unsaved_changes_and_inform_user()

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
        