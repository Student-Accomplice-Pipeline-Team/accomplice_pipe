
import os
import re
import logging
log = logging.getLogger(__name__)

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
    log.info('creating new symlink at ' + sym_path + '. Linked to ' + new_version_path)
    os.remove(sym_path)
    os.symlink(new_version_path, sym_path)


