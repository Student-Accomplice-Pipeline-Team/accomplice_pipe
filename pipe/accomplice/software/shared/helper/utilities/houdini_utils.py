import hou
import os
from pathlib import Path
import pipe
from ...object import Shot
# from pipe.shared.proxy import proxy

# server = proxy.get_proxy()
server = pipe.server

class HoudiniFXUtils():
    supported_FX_names = ['sparks', 'smoke', 'money']

class HoudiniNodeUtils():
    current_node_definitions = {
        'reference': 'reference::2.0',
        'pxrsurface': 'pxrsurface::3.0',
        'filecache': 'filecache::2.0',

        # FX Materials:
        'money_material': 'accomp_money_material::1.0',
        'sparks_material': 'accomp_sparks_material::1.0',
        'smoke_material': 'accomp_smoke_material::1.0',

        # Money automation helpers:
        'money_apply_rotations': 'money_apply_rotations::1.0',
        'money_post_process': 'money_post_process::1.0'
    }

    def get_node_definition_name(base_name: str) -> str:
        if base_name in HoudiniNodeUtils.current_node_definitions:
            return HoudiniNodeUtils.current_node_definitions[base_name]
        return base_name
    
    def create_node(parent_node: hou.Node, base_name: str, override_name = False) -> hou.Node:
        if override_name:
            print('Creating node... ', base_name)
            return parent_node.createNode(base_name)
        node_definition_name = HoudiniNodeUtils.get_node_definition_name(base_name)
        print('Creating node... ', node_definition_name)
        return parent_node.createNode(node_definition_name)

class HoudiniPathUtils():
    @staticmethod
    def get_fx_usd_cache_folder_path():
        shot_name = HoudiniUtils.get_shot_name()
        if shot_name is None:
            return None
        shot = server.get_shot(shot_name)
        main_fx_folder_location = shot.get_fx_usd_cache_directory_path()
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
    
class HoudiniUtils:
    @staticmethod
    def get_shot_name() -> str:
        """ Returns the shot name based on the current Houdini session's file path """
        my_path = hou.hipFile.path()
        from .file_path_utils import FilePathUtils
        return FilePathUtils.get_shot_name_from_file_path(my_path)
    
    @staticmethod
    def get_shot_for_file() -> Shot:
        return server.get_shot(HoudiniUtils.get_shot_name())