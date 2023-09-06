import hou
import os
from pathlib import Path
from pipe.shared.proxy import proxy

server = proxy.get_proxy()

class HoudiniNodeUtils():
    pass

class HoudiniPathUtils():
    @staticmethod
    def get_fx_usd_cache_folder_path():
        shot_name = HoudiniPathUtils.get_shot_name()
        if shot_name is None:
            return None
        shot = server.get_shot(shot_name)
        main_fx_folder_location = shot.get_fx_usd_cache_path()
        if main_fx_folder_location is None:
            return None
        
        # Create the folder (or do nothing if it already exists)
        Path(main_fx_folder_location).mkdir(parents=True, exist_ok=True)
        return main_fx_folder_location
    
    @staticmethod
    def get_fx_usd_cache_file_path(base_name):
        folder_path = HoudiniPathUtils.get_fx_usd_cache_folder_path()
        if folder_path is None:
            return None
        return os.path.join(folder_path, f"{base_name}.usd")
    
    @staticmethod
    def get_shot_name():
        my_path = hou.hipFile.path()
        from .file_path_utils import FilePathUtils
        return FilePathUtils.get_shot_name_from_file_path(my_path)