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
    def __init__(self, symbolic_file_location):
        """
        Initializes an instance of the class.

        Args:
            symbolic_file_location (str): The location of the file that we are encapsulating in this version manager.
        Returns:
            None
        """

        assert os.path.exists(symbolic_file_location), "The file at the given location does not exist."

        log.info('Initializing Version Manager for ' + symbolic_file_location)

        self.sym_path = symbolic_file_location
        self.file_name_without_extension = pathlib.Path(self.sym_path).stem
        self.versions_folder = os.path.join(os.path.dirname(self.sym_path), '.versions', os.path.basename(self.sym_path).split('.')[0])

        # If it doesn't exist, create it.
        if not pathlib.Path(self.versions_folder).exists():
            pathlib.Path(self.versions_folder).mkdir(parents=True, exist_ok=True)

        # If the path given is not a symbolic link, we need to create one.
        if not pathlib.Path(self.sym_path).is_symlink():
            # Copy the file to the verions folder and create a symbolic link to it.
            new_version_path = self.get_next_version()
            assert not os.path.exists(new_version_path), "The file already exists in the versions folder."
            shutil.copy(self.sym_path, new_version_path)

            # Also copy to a backups folder
            backups_folder = os.path.join(os.path.dirname(self.sym_path), '.backups')
            if not os.path.exists(backups_folder):
                os.makedirs(backups_folder)
            shutil.copy(self.sym_path, os.path.join(backups_folder, os.path.basename(self.sym_path)))

            self.update_symlink(new_version_path)
            
        # If the version note file doesn't exist, create it.
        self.version_note_file = os.path.join(self.versions_folder, self.file_name_without_extension + '_version_notes.json')
        if not os.path.exists(self.version_note_file):
            with open(self.version_note_file, 'w') as f:
                json.dump(
                    {
                        1: 'First version.'
                    }
                    ,
                    f
                )
        
        self._semaphore = threading.Semaphore()
        # self.is_editing = False

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
        return os.path.realpath(self.sym_path)
    
    def get_current_version_number(self):
        return extract_version(self.get_current_version_path())[0]
    
    def get_current_version_timestamp(self):
        return os.path.getmtime(self.get_current_version_path())
    
    def get_all_versions_associated_with_file(self):
        return [os.path.join(self.versions_folder, f) for f in os.listdir(self.versions_folder) if f.startswith(self.file_name_without_extension) and not f.endswith('.json')]
    
    def get_version_table(self):
        """
        Returns a list of tuples containing the file, version number, the timestamp, and the note.
        """
        return [(f, extract_version(f)[0], os.path.getmtime(f), self.get_note_for_version(extract_version(f)[0])) for f in self.get_all_versions_associated_with_file()]
    
    def get_file_for_version(self, version_number:int):
        """
        Returns the path to the version with the given version number.
        """
        matching_files = [f for f in self.get_all_versions_associated_with_file() if extract_version(f)[0] == version_number]
        print(matching_files)
        assert len(matching_files) == 1, "There should only be one file with the given version number."
        return matching_files[0]
    
    def get_next_version(self):
        """
        Returns the path to the next version of the file.
        """
        return get_next_version(self.sym_path)
    
    def update_symlink(self, new_version_path):
        """
        Updates the symlink to point to the given file.
        """
        update_symlink(self.sym_path, new_version_path)

    def save_new_version(self, version_note=None):
        """
        Saves a new version of the file.
        """
        with self._semaphore:
            print('my stack trace:')
            new_version_path = self.get_next_version()
            assert not os.path.exists(new_version_path), "The file already exists in the versions folder."
            shutil.copy(self.sym_path, new_version_path)
            self.update_symlink(new_version_path)
            
            if version_note:
                self.set_note_for_version(self.get_current_version_number(), version_note)
        
    
    def switch_to_version(self, version_number:int):
        """
        Reverts the file to the given version number.
        """
        new_version_path = self.get_file_for_version(version_number)
        assert os.path.exists(new_version_path), "The file does not exist."
        self.update_symlink(new_version_path)