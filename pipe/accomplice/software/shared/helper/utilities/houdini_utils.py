import hou
import os
from pathlib import Path
from pipe.shared.proxy import proxy

server = proxy.get_proxy()

class HoudiniNodeUtils(): # It's more efficient to develop the tool with this class here, but when it's done being edited, you can move it back to the houdini_utils file
    current_node_definitions = {
        'reference': 'reference::2.0',
        'pxrsurface': 'pxrsurface::3.0',
        'sparks_material': 'accomp_sparks_material::1.0',
        'smoke_material': 'accomp_smoke_material::1.0',
        'filecache': 'filecache::2.0'
    }

    def get_node_definition_name(base_name: str) -> str:
        if base_name in HoudiniNodeUtils.current_node_definitions:
            return HoudiniNodeUtils.current_node_definitions[base_name]
        return base_name
    
    def create_node(parent_node: hou.Node, base_name: str, override_name = False) -> hou.Node:
        if not override_name:
            node_definition_name = HoudiniNodeUtils.get_node_definition_name(base_name)
            return parent_node.createNode(node_definition_name)
        return parent_node.createNode(base_name)

class HoudiniPathUtils():
    @staticmethod
    def get_fx_usd_cache_folder_path():
        shot_name = HoudiniPathUtils.get_shot_name()
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
    
    @staticmethod
    def get_entire_shot_fx_usd_path():
        shot_name = HoudiniPathUtils.get_shot_name()
        if shot_name is None:
            return None
        shot = server.get_shot(shot_name)
        return shot.get_shot_fx_usd_path()
    
    @staticmethod
    def get_shot_name():
        my_path = hou.hipFile.path()
        from .file_path_utils import FilePathUtils
        return FilePathUtils.get_shot_name_from_file_path(my_path)