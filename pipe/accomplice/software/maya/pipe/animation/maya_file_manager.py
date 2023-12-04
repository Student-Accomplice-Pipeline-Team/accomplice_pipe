import maya.cmds as cmds
import os
import pathlib
from pipe.shared.versions import VersionManager
import time
from PySide2 import QtWidgets
import pipe
# from pipe.accomplice.software.shared.helper.utilities.ui_utils import ListWithFilter
from pipe.shared.helper.utilities.ui_utils import ListWithFilter, InfoDialog

class MayaFileManager:
    @staticmethod
    def save_new_version():
        # import pdb; pdb.set_trace()
        current_file_path = cmds.file(query=True, sceneName=True)
        if current_file_path:
            vm = VersionManager(current_file_path)

            if MayaFileManager.check_for_unsaved_changes_and_inform_user():
                return
            
            # # Prompt the user for a version note
            # result = cmds.promptDialog(
            #     title='Save Version ' + str(vm.get_current_version_number() + 1),
            #     message='Enter Note for New Version:',
            #     button=['OK', 'Cancel'],
            #     defaultButton='OK',
            #     cancelButton='Cancel',
            #     dismissString='Cancel')

            vm.save_new_version()
            cmds.confirmDialog(title='Version Saved', message='A new version has been saved.', button=['Ok'])
            # if result == 'OK':
            #     version_note = cmds.promptDialog(query=True, text=True)
            # else:
            #     version_note = None


    @staticmethod
    def show_current_version():
        current_file_path = cmds.file(query=True, sceneName=True)
        if current_file_path:
            vm = VersionManager(current_file_path)
            current_version = vm.get_current_version_number()
            cmds.confirmDialog(title='Current Version', message=f'The current version is {current_version}.', button=['Ok'])
    
    @staticmethod
    def switch_version_ui():
        current_file_path = cmds.file(query=True, sceneName=True)
        if current_file_path:
            vm = VersionManager(current_file_path)
            version_table = vm.get_version_table()

            # Sort the version table by timestamp
            version_table_sorted = sorted(version_table, key=lambda x: x[2])  # x[2] is the timestamp

            current_version_number = vm.get_current_version_number()

            if cmds.window("versionSwitchWindow", exists=True):
                cmds.deleteUI("versionSwitchWindow", window=True)

            cmds.window("versionSwitchWindow", title="Switch to Version (Current Version: " + str(current_version_number) + ")")
            cmds.columnLayout(adjustableColumn=True)
            for file, version_number, timestamp, note in version_table_sorted:
                timestamp_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                cmds.button(label=f"Version {version_number} - {timestamp_readable} - Note: {note}", 
                            command=lambda x, vn=version_number: MayaFileManager.switch_to_selected_version(vn))

            cmds.showWindow("versionSwitchWindow")


    @staticmethod
    def switch_to_selected_version(version_number):
        # Ask if they want to save the current version
        if MayaFileManager.check_for_unsaved_changes_and_inform_user():
            return

        cmds.confirmDialog(title='Version Switched', message=f'Switched to version {version_number}.', button=['Ok'])
        if cmds.window("versionSwitchWindow", exists=True):
            cmds.deleteUI("versionSwitchWindow", window=True)
        current_file_path = cmds.file(query=True, sceneName=True)
        vm = VersionManager(current_file_path)
        vm.switch_to_version(version_number)

        # Open the file in Maya
        OpenNewFileManager.open_file(vm.get_main_path())

    @staticmethod
    def edit_version_note():
        current_file_path = cmds.file(query=True, sceneName=True)
        # import pdb; pdb.set_trace()
        if current_file_path:
            vm = VersionManager(current_file_path)
            current_version = vm.get_current_version_number()
            existing_note = vm.get_note_for_version(current_version)

            result = cmds.promptDialog(
                title='Edit Note',
                message=f'Enter Note for Version {current_version}:',
                text=existing_note,
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')

            if result == 'OK':
                new_note = cmds.promptDialog(query=True, text=True)
                vm.set_note_for_version(current_version, new_note)
                # cmds.confirmDialog(title='Note Updated', message='The note has been updated.', button=['Ok'])
    
    @staticmethod
    def check_for_unsaved_changes_and_inform_user():
        """
        Checks if the current file has unsaved changes. If it does, informs the user and returns True."""
        if cmds.file(query=True, modified=True):
            cmds.confirmDialog(title='Unsaved Changes', message='The current file has unsaved changes. Please save before continuing.', button=['Ok'])
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
        # vm = VersionManager(file_path) # This ensures that a symlink version is created if it doesn't already exist.

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

        # vm = VersionManager(file_path)
        
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
        