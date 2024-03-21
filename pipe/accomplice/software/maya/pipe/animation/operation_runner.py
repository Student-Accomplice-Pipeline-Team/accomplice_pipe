from pipe.shared.helper.utilities.ui_utils import ListWithCheckboxFilter
from pipe.animation.maya_file_manager import MayaFileManager
from pipe.animation.logger import SimpleLogger
import maya.cmds as cmds
import pipe
import os

class OperationRunner():
    def __init__(self, operation: callable):
        self.operation = operation
        self.logger = SimpleLogger("OperationRunner")
        self.shots = self.get_shots_to_export()
        if self.shots is None:  # If the dialog was canceled
            self.logger.info("Operation canceled by the user.")
            return

    def get_shots_to_export(self):
        shots = MayaFileManager.get_names_of_all_maya_shots_that_have_been_created()
        # Filter out the shots with Z or 000 in them
        shots = [shot for shot in shots if "Z" not in shot and "000" not in shot]
        shot_selection_dialog = ListWithCheckboxFilter("Select Which Shots You Would Like To Export", sorted(shots), list_label="Shots", include_filter_field=True)
        result = shot_selection_dialog.exec_()

        if not result:  # Assuming exec_ returns False or None when canceled
            return None  # Signal that the operation should be canceled

        selected_items = shot_selection_dialog.get_selected_items()
        if not selected_items:  # Check if the user selected nothing and pressed OK, which should also cancel
            return None

        return [pipe.server.get_shot(shot) for shot in selected_items]

    def run(self, *args, **kwargs):
        if not self.shots:  # Check if the initialization process was completed or canceled
            print("Operation aborted due to user cancellation or no shots selected.")
            return  # Exit the function early

        self.logger.info(f'Shots to export: {self.shots}')

        for shot in self.shots:
            self.logger.info(f'Opening shot file for shot {shot.get_name()}')

            # Open the shot file
            file_path = shot.get_maya_shotfile_path()

            # Ensure the file exists
            if not os.path.isfile(file_path):
                self.logger.error(f'File does not exist: {file_path}')
                continue
            
            cmds.file(file_path, open=True, force=True)
            self.logger.info(f'Opened shot file for shot {shot.get_name()}')

            # Run the operation with any additional arguments
            self.operation(*args, **kwargs)
