from pathlib import Path
from pipe.shared.object import Shot
import os

def verify_shot_name(shot_name):
    import pipe
    assert shot_name in pipe.server.get_shot_list()

class FilePathUtils():
    subfile_types = Shot.available_departments
    
    def _get_path_split_and_shots_index(file_path) -> (list, int):
        from os.path import sep as separator
        # Note that the structure of a file path comes in as /groups/accomplice/pipeline/production/sequences/<SEQUENCE_NAME>/shots/<SHOT_NAME>/...
        path_split = file_path.split(separator)
        shots_index = None
        try:
            shots_index = path_split.index("shots")
        except ValueError:
            return path_split, None
        return path_split, shots_index

    @staticmethod
    def get_shot_name_from_file_path(file_path) -> str or None:
        """ Returns the shot name from a file path """

        path_split, shots_index = FilePathUtils._get_path_split_and_shots_index(file_path)
        if shots_index is None:
            # This file path does not contain a shot name
            return None

        # So, the shot_name is composed of <SEQUENCE_NAME>_<SHOT_NAME>
        shot_name = path_split[shots_index - 1] + '_' + path_split[shots_index + 1]

        verify_shot_name(shot_name)

        return shot_name
    
    def get_department_from_file_path(file_path) -> str or None:
        """ Returns the department from a file path """
        path_split, shots_index = FilePathUtils._get_path_split_and_shots_index(file_path)
        if shots_index is None:
            # This file path does not contain a shot name
            return None
        
        try:
            # Note that the structure of a file path comes in as /groups/accomplice/pipeline/production/sequences/<SEQUENCE_NAME>/shots/<SHOT_NAME>/<DEPARTMENT>/...
            department_from_path = path_split[shots_index + 2]
        except IndexError:
            return None
        
        if department_from_path == os.path.basename(file_path):
            return 'main'
        
        assert department_from_path in FilePathUtils.subfile_types

        return department_from_path