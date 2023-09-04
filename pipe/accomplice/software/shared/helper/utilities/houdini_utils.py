import hou
import os
import pipe

USD_CACHE_FOLDER_NAME = "usd_cache"

class HoudiniNodeUtils():
    """ The location of static methods for use with houdini nodes that are likely to be called in a variety of places """
    pass

class HoudiniPathUtils():
    @staticmethod
    def get_fx_usd_cache_folder_path():
        my_path = hou.hipFile.path()
        from .file_path_utils import FilePathUtils
        shot_name = FilePathUtils.get_shot_name_from_file_path(my_path)
        if shot_name is None:
            return None
        shot = pipe.server.get_shot(shot_name)
        main_fx_folder_location = os.path.dirname(shot.get_shotshotfile(type='fx'))
        return os.path.join(main_fx_folder_location, USD_CACHE_FOLDER_NAME)
    
    @staticmethod
    def get_fx_usd_cache_file_path(base_name):
        folder_path = HoudiniPathUtils.get_fx_usd_cache_folder_path()
        if folder_path is None:
            return None
        return os.path.join(folder_path, f"{base_name}.usd")