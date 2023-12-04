import os
import shutil
import re
import logging
log = logging.getLogger(__name__)
import pathlib
import json
import threading

#Returns the file name of the latest version in the .versions folder
def get_current_version(sym_path):
    if os.path.exists(sym_path):

        file_name = os.path.basename(sym_path)
        folder = sym_path.replace(file_name, '')
        versions_folder = os.path.join(folder, '.versions', file_name.split('.')[0])

        if not os.path.exists(versions_folder):
            log.error("No versions exist for this sym_link path.")
            return

        files = os.listdir(versions_folder)
        if files:
            latest_version = max(files,key=extract_version)
            
            return latest_version
        else:
            log.error("Versions folder is empty")
            return
    
    else:
        log.error("There is no file at this path.")
        return

#Returns a tuple of the int value of the version and the basename of the file
def extract_version(f):
    s = re.findall('(?<=_v)[0-9]+(?=\.)', f)
    return (int(s[0]) if s else -1,f)

#Returns the file path of the next highest version based on the path to a given symlink.
#   - If the versions folder doesn't exist, one is created
def get_next_version(sym_path):
    file_name = os.path.basename(sym_path)
    folder = sym_path.replace(file_name, '')
    versions_folder = os.path.join(folder, '.versions', file_name.split('.')[0])

    if not os.path.exists(versions_folder):
        os.makedirs(versions_folder)

    current_version = get_current_version(sym_path)

    if not current_version:
        latest_int = 0
    
    else:
        latest_int = extract_version(current_version)[0]

    new_file_name = file_name.split('.')[0] + '_v' + str(latest_int + 1).zfill(3) + '.' + file_name.split('.')[1]

    return os.path.join(versions_folder, new_file_name)

#Deletes current symlink and creates a new one linked to the given file. 
def update_symlink(sym_path, new_version_path):
    import traceback
    traceback.print_stack()
    log.info('Updating symlink at ' + sym_path + '. Linked to ' + new_version_path)
    if os.path.exists(sym_path):
        os.remove(sym_path)
    os.symlink(new_version_path, sym_path)



class VersionManager:
    """
    This class is responsible for managing versions of a file. Note that is uses symlinks only to make it clear what the current version is (the file representing the current version points to the main_file), but it could operate just the same without the symlink.
    """
    def __init__(self, current_file_location):
        """
        Initializes an instance of the class.

        Args:
            current_file_location (str): The location of the file that we are encapsulating in this version manager.
        Returns:
            None
        """

        assert os.path.exists(current_file_location), "The file at the given location does not exist."

        log.info('Initializing Version Manager for ' + current_file_location)

        self.main_path = current_file_location
        self.file_name_without_extension = pathlib.Path(self.main_path).stem
        self.versions_folder = os.path.join(os.path.dirname(self.main_path), '.versions', self.file_name_without_extension)

        # If it doesn't exist, create it.
        if not pathlib.Path(self.versions_folder).exists():
            pathlib.Path(self.versions_folder).mkdir(parents=True, exist_ok=True)

        # If the version note file doesn't exist, create it.
        self.version_note_file = os.path.join(self.versions_folder, self.file_name_without_extension + '_version_notes.json')
        if not os.path.exists(self.version_note_file):
            self.initialize_version_manager_file_system()
    
    def initialize_version_manager_file_system(self):
        # If this file doesn't exist, we can assume that this is the first version.
        with open(self.version_note_file, 'w') as f:
            json.dump(
                {
                    0: 'First version.', # The key is the version number, the value is the note.
                    'current_version': 0 # This is the current version number, which changes if users change the file version
                        
                }
                ,
                f
            )

        # This will give us the path to a first version
        new_version_path = self.get_next_version_path()
        assert not os.path.exists(new_version_path), "The file already exists in the versions folder."
        # shutil.copy(self.main_path, new_version_path)
        # The current version in the versions folder is just a symlink to the actual file
        os.symlink(self.main_path, new_version_path)

        self.create_backup()

        assert self.get_version_number_for_file_path(new_version_path) == self.get_current_version_number(), "The version number of the new file is not correct."
        assert self.get_version_number_for_file_path(new_version_path) == 0, "The version number of the new file is not correct."
        self._set_version(self.get_version_number_for_file_path(new_version_path))

    def create_backup(self):
        # Also copy to a backups folder just in case :)
        backups_folder = os.path.join(os.path.dirname(self.main_path), '.backups')
        if not os.path.exists(backups_folder):
            os.makedirs(backups_folder)
        shutil.copy(self.main_path, os.path.join(backups_folder, os.path.basename(self.main_path)))
        log.info('Created backup of ' + self.main_path + ' at ' + os.path.join(backups_folder, os.path.basename(self.main_path)))
    
    
    def get_main_path(self):
        """
        Returns the path to the main file.
        """
        return self.main_path

    def _set_version(self, version_number:int):
        """
        Sets the current version number but does not switch the version
        """
        with open(self.version_note_file, 'r') as f:
            notes = json.load(f)
            notes['current_version'] = version_number
        with open(self.version_note_file, 'w') as f:
            json.dump(notes, f)
        log.info('Set current version to ' + str(version_number))
    
    def get_version_number_for_file_path(self, file_path:str):
        """
        Returns the version number for the given file path.
        """
        return extract_version(file_path)[0]

    def get_note_for_version(self, version_number:int):
        """
        Returns the note associated with the given version number.
        """
        with open(self.version_note_file, 'r') as f:
            notes = json.load(f)
            if str(version_number) not in notes:
                return ''
            return notes[str(version_number)]

    def set_note_for_version(self, version_number:int, note:str):
        """
        Sets the note associated with the given version number.
        """
        notes = json.load(open(self.version_note_file, 'r'))
        notes[str(version_number)] = note
        with open(self.version_note_file, 'w') as f:
            json.dump(notes, f)
    
    def get_current_version_path(self):
        current_version = self.get_current_version_number()
        path = self.get_path_for_version(current_version)
        return path
    
    def get_current_version_number(self):
        """
        Returns the current version number.
        """
        with open(self.version_note_file, 'r') as f:
            notes = json.load(f)
            assert 'current_version' in notes, "The current version number is not in the version note file."
            return notes['current_version']
    
    def get_current_version_timestamp(self):
        return os.path.getmtime(os.path.realpath(self.get_current_version_path()))
    
    def get_all_versions_associated_with_file(self):
        return [os.path.join(self.versions_folder, f) for f in os.listdir(self.versions_folder) if f.startswith(self.file_name_without_extension) and not f.endswith('.json')]
    
    def get_version_table(self):
        """
        Returns a list of tuples containing the file, version number, the timestamp, and the note.
        """
        return [(f, extract_version(f)[0], os.path.getmtime(os.path.realpath(f)), self.get_note_for_version(extract_version(f)[0])) for f in self.get_all_versions_associated_with_file()]
    
    def get_path_for_version(self, version_number:int):
        """
        Returns the path to the version with the given version number.
        """
        matching_files = [f for f in self.get_all_versions_associated_with_file() if self.get_version_number_for_file_path(f) == version_number]
        print(matching_files)
        assert len(matching_files) == 1, "There should only be one file with the given version number."
        return matching_files[0]
    
    def get_next_version_path(self):
        """
        Returns the path to the next version of the file.
        """
        return get_next_version(self.main_path)

    def save_new_version(self, version_note=None):
        """
        Saves a new version of the file.
        """
        new_version_path = self.get_next_version_path()
        new_version_number = self.get_version_number_for_file_path(new_version_path)
        assert not os.path.exists(new_version_path), "The file already exists in the versions folder."
        shutil.copy(self.main_path, new_version_path) # At this point, the new version is just a copy of the current version
        self.switch_to_version(new_version_number) # Obviously there are a couple more copies being made here than necessary, but it's fine for now.
        
        if version_note:
            self.set_note_for_version(self.get_current_version_number(), version_note)
        
    
    def switch_to_version(self, version_number:int):
        """
        Reverts the file to the given version number.
        """
        # Copy the current file to the current version
        previous_version_path = self.get_path_for_version(self.get_current_version_number())
        assert os.path.exists(previous_version_path), "The file does not exist."
        assert os.path.islink(previous_version_path), "The file is not a symlink."
        os.remove(previous_version_path) # remove the symlink
        # Copy the current file to the previous path
        shutil.copy(self.main_path, previous_version_path)
        log.info('Copied ' + self.main_path + ' to ' + previous_version_path)
        # Remove the main path and copy the new version to the main path
        self.create_backup()

        os.remove(self.main_path)
        new_version_path = self.get_path_for_version(version_number)
        assert os.path.exists(new_version_path), "The file does not exist."
        shutil.copy(new_version_path, self.main_path)
        log.info('Copied ' + new_version_path + ' to ' + self.main_path)
        # Remove the new_version_path and make it a symlink instead
        os.remove(new_version_path)
        os.symlink(self.main_path, new_version_path)
        log.info('Made a symlink at ' + new_version_path + ' to ' + self.main_path)
        self._set_version(version_number)