import hou
import os
from pathlib import Path
import pipe
from ...object import Shot
from .file_path_utils import FilePathUtils
from abc import ABC, abstractmethod
# from pipe.shared.proxy import proxy

# server = proxy.get_proxy()
server = pipe.server

class HoudiniFXUtils():
    supported_FX_names = ['sparks', 'smoke', 'money']
    
    @staticmethod
    def get_fx_usd_cache_directory_path(shot: Shot):
        USD_CACHE_FOLDER_NAME = "usd_cache"
        fx_directory = shot.get_shotfile_folder('fx')
        return os.path.join(fx_directory, USD_CACHE_FOLDER_NAME)
    
    @staticmethod
    def get_car_fbx_transform_path(shot):
        # cfx_folder = self.get_shotfile_folder('cfx')
        # return os.path.join(cfx_folder, 'car_transform_test.fbx') # TODO: update this when you know the naming convention
        return "/groups/accomplice/pipeline/production/sequences/A/shots/180/cfx/car_transform_test.fbx"

    



class HoudiniNodeUtils():
    def __init__(self):
        pass
    current_node_definitions = {
        'reference': 'reference::2.0',
        'pxrsurface': 'pxrsurface::3.0',
        'filecache': 'filecache::2.0',

        # FX Materials:
        'money_material': 'accomp_money_material::1.0',
        'sparks_material': 'accomp_sparks_material::1.0',
        'smoke_material': 'accomp_smoke_material::1.0',
        'skid_marks_material': 'accomp_skid_marks_material::1.0',
    }

    def link_parm(source_node: hou.Node, target_node: hou.Node, parm: str):
        # import pdb; pdb.set_trace()
        target_parm = target_node.parm(parm)
        expression = 'ch("' + source_node.path() + '/' + parm + '")'
        target_parm.setExpression(expression)

    def link_parms(source_node: hou.Node, target_node: hou.Node, parms: list):
        for parm in parms:
            HoudiniNodeUtils.link_parm(source_node, target_node, parm)

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

    def node_exists(parent: hou.Node, node_name: str) -> bool:
        return parent.node(node_name) is not None
    
    def configure_new_scene(shot: Shot, department_name:str=None):
        # Create a new scene
        if department_name != 'main' and department_name is not None:
            new_scene_creator = HoudiniNodeUtils.DepartmentSceneCreator(shot, department_name)
        else:
            new_scene_creator = HoudiniNodeUtils.MainSceneCreator(shot)
        new_scene_creator.create()

    class NewSceneCreator(ABC):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('stage')):
            self.shot = shot
            self.stage = stage
            self.my_created_nodes = []
        
        @abstractmethod
        def add_nodes(self):
            pass

        def create(self):
            self.add_nodes()
            self.stage.layoutChildren(items=self.my_created_nodes)

        def create_load_shot_node(self):
            load_shot_node = HoudiniNodeUtils.create_node(self.stage, 'accomp_load_shot_usds')
            self.my_created_nodes.append(load_shot_node)
            return load_shot_node

    class MainSceneCreator(NewSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node = hou.node('stage')):
            super().__init__(shot, stage)
        
        def add_nodes(self):
            load_shot_node = self.create_load_shot_node()
            self.create_main_usd_rop_node(load_shot_node)

        def create_main_usd_rop_node(self, input_node: hou.Node):
            # Add the usd rop node
            if self.shot is not None:
                usd_rop_node = input_node.createOutputNode('usd_rop', 'OUT_' + self.shot.name)
                usd_rop_node.parm("trange").set(1) # Set the time range to include the entire frame range
                usd_rop_node.parm("lopoutput").set(self.shot.get_shot_usd_path())
                
                self.my_created_nodes.append(usd_rop_node)
                return usd_rop_node

    class DepartmentSceneCreator(NewSceneCreator):
        def __init__(self, shot: Shot, department_name: str, stage: hou.Node=hou.node('stage')):
            self.department_name = department_name
            super().__init__(shot, stage)
        
        # Override
        def add_nodes(self):
            load_shot_node = self.create_load_shot_node()
            configure_department_scene_graph = self.create_configure_scene_graph_node()
            self.create_department_usd_rop_node(configure_department_scene_graph)
            merge_node = self.create_merge_node(load_shot_node, configure_department_scene_graph)

        def create_department_usd_rop_node(self, configure_department_scene_graph: hou.Node):
            # Add the usd rop node
            usd_rop_node = configure_department_scene_graph.createOutputNode('usd_rop', 'OUT_' + self.shot.name + '_' + self.department_name)
            usd_rop_node.parm("trange").set(1) # Set the time range to include the entire frame range
            usd_rop_node.parm("lopoutput").set(self.shot.get_shot_usd_path(self.department_name))
            
            self.my_created_nodes.append(usd_rop_node)
            return usd_rop_node

        def create_configure_scene_graph_node(self):
            # Create a null node for the department work coming in
            in_department_work = HoudiniNodeUtils.create_node(self.stage, 'null')
            in_department_work.setName('IN_' + self.department_name)
            self.my_created_nodes.append(in_department_work)

            configure_department_scene_graph = in_department_work.createOutputNode('accomp_configure_department_scene_graph', 'configure_scene_graph')
            self.my_created_nodes.append(configure_department_scene_graph)

            return configure_department_scene_graph

        def create_merge_node(self, load_shot_node: hou.Node, configure_department_scene_graph: hou.Node):
            # Create a merge node
            merge_node = HoudiniNodeUtils.create_node(hou.node('stage'), 'merge')

            # Connect 2nd output of configure_department_scene_graph to the merge node
            merge_node.setInput(0, configure_department_scene_graph, output_index=1)

            # Set the second input to the merge to be the load_shot_node:
            merge_node.setInput(1, load_shot_node)
            self.my_created_nodes.append(merge_node)

            # Create a null node called 'OUT_entire_scene_preview'
            out_entire_scene_preview = merge_node.createOutputNode('null', 'OUT_entire_scene_preview')
            out_entire_scene_preview.setDisplayFlag(True)
            self.my_created_nodes.append(out_entire_scene_preview)
            return merge_node
            

class HoudiniPathUtils():
    @staticmethod
    def get_fx_usd_cache_folder_path():
        shot_name = HoudiniUtils.get_shot_name()
        if shot_name is None:
            return None
        shot = server.get_shot(shot_name)
        main_fx_folder_location = HoudiniFXUtils.get_fx_usd_cache_directory_path(shot)
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
    def _get_my_path():
        return hou.hipFile.path()
    
    @staticmethod
    def get_shot_name() -> str or None:
        """ Returns the shot name based on the current Houdini session's file path """
        my_path = HoudiniUtils._get_my_path()
        return FilePathUtils.get_shot_name_from_file_path(my_path)
    
    @staticmethod
    def get_department() -> str or None:
        """ Returns the department from a file path """
        return FilePathUtils.get_department_from_file_path(HoudiniUtils._get_my_path())
    
    @staticmethod
    def get_shot_for_file(retrieve_from_shotgrid=False) -> Shot or None:
        shot_name = HoudiniUtils.get_shot_name()
        if shot_name is None:
            return None
        return server.get_shot(HoudiniUtils.get_shot_name(), retrieve_from_shotgrid=retrieve_from_shotgrid)

    @staticmethod
    def check_for_unsaved_changes():
        if hou.hipFile.hasUnsavedChanges():
            warning_response = hou.ui.displayMessage(
                "The current file has not been saved. Continue anyway?",
                buttons=("Continue", "Cancel"),
                severity=hou.severityType.ImportantMessage,
                default_choice=1
            )
            return warning_response

    @staticmethod
    def prompt_user_for_shot():
        shot_names = sorted(pipe.server.get_shot_list())
        shot_response = hou.ui.selectFromList(
            shot_names,
            exclusive=True,
            message="Select the Shot File that you'd like to open.",
            title="Open Shot File",
            column_header="Shots"
        )
        if shot_response:
            shot_name = shot_names[shot_response[0]]
            shot = pipe.server.get_shot(shot_name, retrieve_from_shotgrid=True)
            return shot
        return None
        
    @staticmethod
    def prompt_user_for_subfile_type() -> str:
        subfile_types = FilePathUtils.subfile_types
        subfile_response = hou.ui.selectFromList(
            subfile_types,
            exclusive=True,
            message="Select the Shot Subfile that you'd like to open.",
            title="Open Shot Subfile",
            column_header="Shot Subfiles"
        )
        if subfile_response:
            subfile_type = subfile_types[subfile_response[0]]
            return subfile_type
        return None