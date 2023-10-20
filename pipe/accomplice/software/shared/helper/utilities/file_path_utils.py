from pathlib import Path
from pipe.shared.object import Shot
import os

def verify_shot_name(shot_name):
    import pipe
    assert shot_name in pipe.server.get_shot_list(), "Shot name " + shot_name + " does not exist in the database."

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
    def get_last_edited_date(file_path) -> float:
        """ Returns the last edited date of a file """
        return Path(file_path).stat().st_mtime
    
    @staticmethod
    def is_file_newer_than_timestamp(file_path, timestamp):
        return FilePathUtils.get_last_edited_date(file_path) > timestamp
    
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
    
    def get_file_matching_substrings(folder_directory:str, substrings:list, enforce_only_one=True) -> list or str:
        """
        Searches for a file in the given folder directory that contains all the given substrings in its name.
        
        Args:
        - folder_directory (str): The directory to search for the file in.
        - substrings (list): A list of substrings that the file name should contain.
        - enforce_only_one (bool): If True, raises an AssertionError if more than one file is found.
        
        Returns:
        - If enforce_only_one is True, returns the path of the file that matches all the substrings.
        - If enforce_only_one is False, returns a list of paths of all the files that match all the substrings.
        """
        # Walk through all files in the subdirectories of the folder directory
        found_files = []
        for root, dirs, files in os.walk(folder_directory):
            for file in files:
                # Check if the file contains all the substrings
                if all(substring.lower() in file.lower() for substring in substrings):
                    found_files.append(os.path.join(root, file))
        
        if enforce_only_one:
            assert len(found_files) == 1, "Found more than one file matching the given substrings: " + str(found_files)
            return found_files[0]

        return found_files
        