import hou
import os
import re
from pathlib import Path
import pipe
from ...object import Shot
from .file_path_utils import FilePathUtils
from .ui_utils import ListWithCheckboxFilter
from .usd_utils import UsdUtils
from abc import ABC, abstractmethod
from .ui_utils import ListWithFilter
from pipe.shared.helper.utilities.dcc_version_manager import DCCVersionManager
import os
import subprocess
import toolutils


class HoudiniFXUtils():
    supported_FX_names = ['sparks', 'smoke', 'money', 'skid_marks', 'leaves_and_gravel', 'background_cop_cars']
    FX_PREFIX = "/scene/fx"

    @staticmethod
    def perform_operation_on_selected_shots(operation: callable, title: str, shot_file_type:str, save_after_operation = False):
        all_shots = sorted(pipe.server.get_shot_list())
        shot_selector = ListWithCheckboxFilter(title, all_shots)

        missing_shots = []
        errored_shots = []
        error_messages = []

        if shot_selector.exec_():
            selected_shots = shot_selector.get_selected_items()
            selected_shots = [Shot(shot) for shot in selected_shots]

            for shot in selected_shots:
                lighting_file_path = shot.get_shotfile(shot_file_type)
                if not os.path.exists(lighting_file_path):
                    missing_shots.append(shot.name)
                    continue
                try:
                    HoudiniUtils.perform_operation_on_houdini_file(
                        lighting_file_path,
                        save_after_operation,
                        operation
                    )
                    print("Completed operation on shot " + shot.name)
                except Exception as e:
                    errored_shots.append(shot.name)
                    error_messages.append(str(e))

        print("These are the missing shots " + str(missing_shots))
        print("These are the errored shots " + str(list(zip(errored_shots, error_messages))))

    @staticmethod
    def user_interface_for_resolving_missing_sublayers():
        sequences = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']  # default sequences
        sequence_selector = ListWithCheckboxFilter("Select Sequences", sequences)
        if sequence_selector.exec_():
            selected_sequences = sequence_selector.get_selected_items()

            # Step 2: Find missing sublayers for the selected sequences
            missing_sublayers = HoudiniFXUtils.get_fx_usds_missing_sublayers(selected_sequences)

            # Convert missing sublayers to a list of shot names
            missing_shots = [layer['shot'] + ' (missing: ' + ', '.join(layer['missing_fx']) + ')' for layer in missing_sublayers]

            # Step 3: Get shot choices from the user
            shot_selector = ListWithCheckboxFilter("Select Shots", missing_shots, items_checked_by_default=True)
            if shot_selector.exec_():
                selected_shots = shot_selector.get_selected_items()
                selected_shots = [selected_shot.split(' ')[0] for selected_shot in selected_shots]

                # Step 4: Resolve missing sublayers for the selected shots
                for shot_name in selected_shots:
                    shot = Shot(shot_name)  # Implement this function based on your data structure
                    HoudiniFXUtils.resolve_missing_sublayers(shot)
    
    @staticmethod
    def resolve_missing_sublayers(shot: Shot):
        def callback(shot: Shot):
            HoudiniFXUtils.insert_missing_cached_fx_into_main_fx_file(shot)
            # Find the USD rop and hit render
            HoudiniUtils.hyper_rop()
            # usd_rop_candidates = HoudiniNodeUtils.find_nodes_of_type(hou.node('/stage'), 'usd_rop')
            # selected_usd_rop = None
            # for usd_rop in usd_rop_candidates:
            #     if usd_rop.parm('lopoutput').eval() == shot.get_shot_usd_path('fx'):
            #         selected_usd_rop = usd_rop
            #         break
            # if selected_usd_rop is not None:
            #     selected_usd_rop.parm('execute').pressButton()

        print(f"Adding missing sublayers to shot {shot.name}")
        main_fx_file = shot.get_shotfile('fx')
        if not os.path.exists(main_fx_file):
            hou.hipFile.save()
            hou.hipFile.clear(suppress_save_prompt=True)
            hou.hipFile.save(main_fx_file)
            HoudiniUtils.configure_new_shot_file(shot, 'fx')
            hou.hipFile.save()
        HoudiniUtils.perform_operation_on_houdini_file(
            main_fx_file,
            True,
            callback,
            shot
        )
    
    @staticmethod
    def get_fx_usds_missing_sublayers(sequences_to_include=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']) -> list:
        fx_usds_missing_sublayers = []
        all_shots = [Shot(shot) for shot in pipe.server.get_shot_list()]
        for shot in all_shots:
            if not shot.name[0] in sequences_to_include:
                continue
            fx_usd = shot.get_shot_usd_path('fx')
            print(f"Checking {fx_usd}")
            cached_fxs = [os.path.basename(path) for path in HoudiniFXUtils.get_paths_to_cached_fx(shot)]
            missing_fx_in_layer = []
            for cached_fx in cached_fxs:
                print(f"Checking if {cached_fx} is in {fx_usd}")
                cached_fx_name = cached_fx.replace('.usd', '')
                if cached_fx_name == 'leaves_and_gravel':
                    if not UsdUtils.is_primitive_in_usd(fx_usd, f"{HoudiniFXUtils.FX_PREFIX}/{'leaves'}"):
                        print(f"{cached_fx} is not in {fx_usd}")
                        missing_fx_in_layer.append(cached_fx)
                else:
                    if not UsdUtils.is_primitive_in_usd(fx_usd, f"{HoudiniFXUtils.FX_PREFIX}/{cached_fx_name}"):
                        print(f"{cached_fx} is not in {fx_usd}")
                        missing_fx_in_layer.append(cached_fx)
            if len(missing_fx_in_layer) > 0:
                fx_usds_missing_sublayers.append(
                    {
                        'usd': fx_usd,
                        'missing_fx': missing_fx_in_layer,
                        'shot': shot.name
                    }
                )
        return fx_usds_missing_sublayers
    
    @staticmethod
    def get_fx_usd_cache_directory_path(shot: Shot):
        USD_CACHE_FOLDER_NAME = "usd_cache"
        fx_directory = shot.get_shotfile_folder('fx')
        return os.path.join(fx_directory, USD_CACHE_FOLDER_NAME)
    
    @staticmethod
    def get_paths_to_cached_fx(shot: Shot):
        fx_usd_cache_directory_path = HoudiniFXUtils.get_fx_usd_cache_directory_path(shot)
        if not os.path.isdir(fx_usd_cache_directory_path):
            return []
        return [os.path.join(fx_usd_cache_directory_path, f) for f in os.listdir(fx_usd_cache_directory_path) if os.path.isfile(os.path.join(fx_usd_cache_directory_path, f)) and f.endswith('.usd')]
    
    @staticmethod
    def create_sublayer_nodes_for_cached_fx(shot: Shot, create_only_missing_sublayers=True):
        cached_fx_paths = HoudiniFXUtils.get_paths_to_cached_fx(shot)
        sublayer_nodes = []
        for cached_fx_path in cached_fx_paths:
            cached_fx_name = os.path.basename(cached_fx_path).replace('.usd', '')
            potential_fx_names = [node.name() for node in HoudiniNodeUtils.find_nodes_of_type(hou.node('/stage'), 'sublayer')]
            if create_only_missing_sublayers and cached_fx_name in potential_fx_names:
                continue
            sublayer_node = HoudiniNodeUtils.create_node(hou.node('/stage'), 'sublayer')
            sublayer_node.parm('filepath1').set(cached_fx_path)
            sublayer_node.setName(cached_fx_name, unique_name=True)
            sublayer_nodes.append(sublayer_node)
        return sublayer_nodes
    
    @staticmethod
    def insert_missing_cached_fx_into_main_fx_file(shot: Shot) -> list:
        created_nodes = []
        sublayer_nodes = HoudiniFXUtils.create_sublayer_nodes_for_cached_fx(shot)
        begin_null, end_null = HoudiniFXUtils.get_fx_range_nulls()
        for sublayer_node in sublayer_nodes:
            HoudiniNodeUtils.insert_node_before(end_null, sublayer_node)
            created_nodes.append(sublayer_node)
        hou.node('/stage').layoutChildren()
        return created_nodes
    
    @staticmethod
    def get_fx_working_directory(shot: Shot):
        FX_WORKING_FOLDER_NAME = "working_files"
        fx_directory = shot.get_shotfile_folder('fx')
        fx_working_folder = os.path.join(fx_directory, FX_WORKING_FOLDER_NAME)
        os.makedirs(fx_working_folder, exist_ok=True)
        return fx_working_folder
    
    @staticmethod
    def get_names_of_fx_files_in_working_directory(shot: Shot):
        # Find all the files in the working directory that end with '.hipnc' and return the names of the files without the extension
        EXTENSION = '.hipnc'
        fx_working_directory = HoudiniFXUtils.get_fx_working_directory(shot)
        assert os.path.exists(fx_working_directory)
        fx_files = [f for f in os.listdir(fx_working_directory) if os.path.isfile(os.path.join(fx_working_directory, f)) and f.endswith(EXTENSION)]
        fx_file_names = [f.replace(EXTENSION, '') for f in fx_files]
        return fx_file_names
    
    @staticmethod
    def get_working_file_path(shot: Shot, fx_name: str):
        return os.path.join(HoudiniFXUtils.get_fx_working_directory(shot), fx_name + '.hipnc' if not fx_name.endswith('.hipnc') else fx_name)
    
    @staticmethod
    def get_fx_name_from_working_file_path(file_path: str):
        return os.path.basename(file_path).replace('.hipnc', '')
    
    @staticmethod
    def open_houdini_fx_file():
        HoudiniUtils.open_shot_file(department_name='fx')

    @staticmethod
    def get_fx_range_nulls():
        return hou.node('/stage').node('BEGIN_fx'), hou.node('/stage').node('END_fx')

    # This file uses the template method pattern to setup the USD wrapper for a given effect
    class USDEffectWrapper(ABC):
        def __init__(self, null_node: hou.Node):
            print('Initializing USDEffectWrapper')
            self.selection = null_node
            self.null_node = null_node
            self.fx_start_null, self.fx_end_null = HoudiniFXUtils.get_fx_range_nulls()
            assert self.null_node is not None
            assert self.null_node.type().name() == "null"

            self.effect_name = self.get_effect_name(self.null_node.name())
            self.effect_import_node = self.get_import_node()
            self.effect_import_node.setName(self.effect_name, unique_name=True)
            assert self.effect_import_node is not None
            print('Finished initializing USDEffectWrapper')

        def get_materials_node(self):
            materials_node = None
            # TODO: If you try to make a material but are unable to add it, you should display a message to the user and then create a default material subnet
            if self.effect_name in HoudiniFXUtils.supported_FX_names:
                try:
                    materials_node = HoudiniNodeUtils.create_node(self.effect_import_node.parent(), self.effect_name + "_material")
                except:
                    # Inform user that the material could not be created
                    hou.ui.displayMessage("Unable to create material for " + self.effect_name + ". Please create a material manually.")
            else:
                # TODO: This needs to be adjusted to properly put the materials into a subnetwork, but this is just boilerplate for now ;)
                # If nothing else, create a default materials subnetwork with a hint to create materials
                materials_node = self.effect_import_node.parent().createNode('subnet')
                subnetwork_nodes = []

                # Inside the subnetwork node, create a material library node
                material_library_node = HoudiniNodeUtils.create_node(materials_node, 'materiallibrary')
                material_library_node.setName(self.effect_name + "_material_library", unique_name=True)
                material_library_node.parm('matpathprefix').set(HoudiniFXUtils.FX_PREFIX + "/" + self.effect_name + "/materials/")

                # Set input of the material library node to be the input of the subnetwork
                
                subnetwork_nodes.append(material_library_node)


                # Create a pxrsurface node inside the material library node
                pxrsurface_node = material_library_node.createNode('pxrsurface')

                # Create an assign material node and connect it
                assign_material_node = materials_node.createNode('assignmaterial')
                assign_material_node.setInput(0, material_library_node)
                # TODO: Set the material path and the geometry path
                subnetwork_nodes.append(assign_material_node)

                output_node = materials_node.node('output0')
                output_node.setInput(0, assign_material_node)
                subnetwork_nodes.append(output_node)

                materials_node.layoutChildren(subnetwork_nodes)

            return materials_node
        
        def add_auxiliary_nodes(self):
            auxiliary_nodes = [self.effect_import_node]

            # Add a subnetwork indicating a place to add materials
            materials_node = self.get_materials_node()
            if materials_node is not None:
                materials_node.setName(self.effect_name + "_materials", unique_name=True)
                HoudiniNodeUtils.insert_node_between_two_nodes(self.effect_import_node, self.fx_end_null, materials_node)
                auxiliary_nodes.append(materials_node)
            
            # Connect a USD ROP to the LOP node
            # usd_rop_node = HoudiniNodeUtils.create_node(self.effect_import_node.parent(), 'usd_rop')
            # Find the usd rop node that already exists
            usd_rop_node = HoudiniNodeUtils.find_nodes_of_type(self.effect_import_node.parent(), 'usd_rop')[0]
            # usd_rop_node.setInput(0, materials_node)
            usd_rop_node.setName("OUT_" + self.effect_name, unique_name=True)
            
            # Set the range to include the entire timeline
            usd_rop_node.parm('trange').set(1)

            # Set the lop node output file to the save path of the lop node
            usd_path = HoudiniPathUtils.get_fx_usd_cache_file_path(self.effect_name)
            usd_rop_node.parm('lopoutput').set(usd_path)
            auxiliary_nodes.append(usd_rop_node)

            
            # Layout only the associated nodes
            self.effect_import_node.parent().layoutChildren()

        def get_effect_name(self, original_node_name: str):
            return original_node_name.replace("OUT_", "")
        
        @abstractmethod
        def get_import_node(self) -> hou.Node:
            pass

        def wrap(self):
            print('Wrapping effect: ' + self.effect_name)
            print('Null node: ' + self.null_node.name())
            assert self.effect_import_node is not None
            assert self.effect_name is not None
            self.add_auxiliary_nodes()
            

    class USDGeometryCacheEffectWrapper(USDEffectWrapper):
        def __init__(self, null_node: list):
            super().__init__(null_node)
        
        def get_import_node(self) -> hou.Node: # Override abstract method
            sop_import_lop = self.create_sop_import_lop()
            HoudiniNodeUtils.insert_node_between_two_nodes(self.fx_start_null, self.fx_end_null, sop_import_lop)
            self.configure_sop_import_lop(sop_import_lop)
            return sop_import_lop

        def create_sop_import_lop(self):
            """Creates SOP Import node from the first node in selection."""
            lop_node = HoudiniNodeUtils.create_node(hou.node('/stage'), 'sopimport')
            return lop_node

        def configure_sop_import_lop(self, lop_node: hou.Node):
            # Set the name of the node
            lop_node_name = self.effect_name
            lop_node.setName(lop_node_name, unique_name=True)
            
            # Set the SOP path
            # path = lop_node.relativePathTo(self.null_node)
            lop_node.parm('soppath').set(self.null_node.path())

            # Set the Import Path Prefix:
            lop_node.parm('pathprefix').set(HoudiniFXUtils.FX_PREFIX + "/" + self.effect_name)

            # Set save path
            lop_node.parm('enable_savepath').set(True)
            lop_node.parm('savepath').set("$HIP/geo/usd_imports/" + self.effect_name + ".usd")
    
    class LeavesAndGravelUSDGeometryCacheEffectWrapper(USDGeometryCacheEffectWrapper):
        def __init__(self, null_node: hou.Node):
            super().__init__(null_node)
        
        def create_sop_import_lop(self) -> hou.Node:
            lop_node = HoudiniNodeUtils.create_node(hou.node('/stage'), 'accomp_import_leaves_and_gravel')
            return lop_node

        def configure_sop_import_lop(self, lop_node: hou.Node):
            return # It's already configured so do nothing :)
    
    class BackgroundCopCarsUSDGeometryCacheEffectWrapper(USDGeometryCacheEffectWrapper):
        def __init__(self, null_node: hou.Node):
            super().__init__(null_node)
        
        def create_sop_import_lop(self) -> hou.Node:
            lop_node = HoudiniNodeUtils.create_node(hou.node('/stage'), 'accomp_background_cop_cars')
            return lop_node

        def get_materials_node(self):
            # Materials are already included in the USD asset that's referenced in
            return None
        
        def configure_sop_import_lop(self, lop_node: hou.Node):
            return

class HoudiniNodeUtils():
    def __init__(self):
        pass
    current_node_definitions = {
        'reference': 'reference::2.0',
        'pxrsurface': 'pxrsurface::3.0',
        'filecache': 'filecache::2.0',

        # FX Materials:
        'money_material': 'accomp_money_material',
        'sparks_material': 'accomp_sparks_material',
        'smoke_material': 'accomp_smoke_material',
        'leaves_and_gravel_material': 'accomp_leaves_and_gravel_material',
        # 'skid_marks_material': 'accomp_skid_marks_material',
    }

    @staticmethod
    def find_first_node_with_parm_value(parent, node_type, parm_name, parm_value):
        """
        Find the first node of a specific type under a given parent node that has a parameter with a specific value.

        Args:
            parent (hou.Node): The parent node under which to search for the matching node.
            node_type (str): The type of node to search for.
            parm_name (str): The name of the parameter to check for the specific value.
            parm_value (Any): The value to compare the parameter against.

        Returns:
            hou.Node or None: The first node found that matches the criteria, or None if no matching node is found.
        """
        matching_node_types = HoudiniNodeUtils.find_nodes_of_type(parent, node_type)
        for matching_node in matching_node_types:
            if matching_node.parm(parm_name).eval() == parm_value:
                return matching_node
        return None
    
    @staticmethod
    def find_nodes_of_type(parent_node, node_type):
        """
        Searches for all child nodes of a specific type under a given parent node in Houdini.

        Args:
        - parent_path (str): The path of the parent node where the search will begin.
        - node_type (str): The type of nodes to search for.

        Returns:
        - list of hou.Node: A list of nodes of the specified type.
        """

        # Find all child nodes of the specified type
        nodes_of_type = [node for node in parent_node.allSubChildren() if node.type().name().split('::')[0] == node_type]

        return nodes_of_type

    @staticmethod
    def find_first_node_of_type(parent, node_type):
        matching_nodes = HoudiniNodeUtils.find_nodes_of_type(parent, node_type)
        if len(matching_nodes) == 0:
            return None
        return matching_nodes[0]

    @staticmethod
    def find_nodes_name_starts_with(parent, node_name_prefix):
        return [node for node in parent.allSubChildren() if node.name().startswith(node_name_prefix)]
    
    @staticmethod
    def find_first_node_name_starts_with(parent, node_name_prefix):
        matching_nodes = HoudiniNodeUtils.find_nodes_name_starts_with(parent, node_name_prefix)
        if len(matching_nodes) == 0:
            return None
        return matching_nodes[0]
    
    @staticmethod
    def insert_node_after(existing_node: hou.Node, node_to_insert: hou.Node):
        """
        Inserts a new node after an existing node in Houdini.

        Args:
            existing_node (hou.Node): The existing node.
            node_to_insert (hou.Node): The node to insert after the existing node.

        Returns:
            hou.Node: The newly created node.
        """
        HoudiniNodeUtils.insert_node_between_two_nodes(existing_node, existing_node.outputs()[0], node_to_insert)
        return node_to_insert
    
    @staticmethod
    def insert_node_before(existing_node: hou.Node, node_to_insert: hou.Node):
        """
        Inserts a new node before an existing node in Houdini.

        Args:
            existing_node (hou.Node): The existing node.
            node_to_insert (hou.Node): The node to insert before the existing node.

        Returns:
            hou.Node: The newly created node.
        """
        HoudiniNodeUtils.insert_node_between_two_nodes(existing_node.input(0), existing_node, node_to_insert)
        return node_to_insert
    
    @staticmethod
    def insert_node_between_two_nodes(first_node: hou.Node, last_node: hou.Node, node_to_insert: hou.Node):
        """
        Inserts a new node between two existing nodes in Houdini.

        Args:
            first_node (hou.Node): The first node.
            last_node (hou.Node): The last node.
            node_to_insert (hou.Node): The node to insert between the first and last nodes.

        Returns:
            hou.Node: The newly created node.
        """
        node_to_insert.setInput(0, first_node)
        last_node.setInput(0, node_to_insert)
        return node_to_insert

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
        assert shot is not None, "Shot must be defined."
        assert department_name is None or department_name in shot.available_departments, f"Department {department_name} is not available for shot {shot.name}."
        
        new_scene_creator = HoudiniNodeUtils.SceneCreatorFactory(shot, department_name).get_scene_creator()
        new_scene_creator.create()


    class SceneCreatorFactory:
        def __init__(self, shot: Shot, department_name: str, stage: hou.Node=hou.node('/stage')):
            self.shot = shot
            self.department_name = department_name
            self.stage = stage
        
        def get_scene_creator(self):
            if self.department_name == 'main' or self.department_name is None:
                return HoudiniNodeUtils.MainSceneCreator(self.shot, self.stage)
            elif self.department_name == 'lighting':
                return HoudiniNodeUtils.LightingSceneCreator(self.shot, self.stage)
            elif self.department_name == 'anim':
                return HoudiniNodeUtils.AnimSceneCreator(self.shot, self.stage)
            elif self.department_name == 'cfx':
                return HoudiniNodeUtils.CFXSceneCreator(self.shot, self.stage)
            elif self.department_name == 'fx':
                fx_name = HoudiniFXUtils.get_fx_name_from_working_file_path(HoudiniUtils.get_my_path())
                if self.shot.name in fx_name:
                    return HoudiniNodeUtils.MainFXSceneCreator(self.shot, self.stage)
                else:
                    return HoudiniNodeUtils.WorkingFileFXSceneCreator(self.shot, self.stage, fx_name)
            else:
                return HoudiniNodeUtils.DepartmentSceneCreator(self.shot, self.department_name, self.stage)
        
    class NewSceneCreator(ABC):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            self.shot = shot
            self.stage = stage
            self.my_created_nodes = []
            self.load_department_layers_node = None
        
        @abstractmethod
        def add_nodes(self):
            pass

        def create(self):
            self.add_nodes()
            self.stage.layoutChildren(items=self.my_created_nodes)

        def create_load_department_layers_node(self, input_node: hou.Node=None):
            if input_node is None:
                self.load_department_layers_node = HoudiniNodeUtils.create_node(self.stage, 'accomp_load_department_layers')
            else:
                self.load_department_layers_node = input_node.createOutputNode('accomp_load_department_layers')
            self.my_created_nodes.append(self.load_department_layers_node)
            return self.load_department_layers_node

    class MainSceneCreator(NewSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node = hou.node('/stage')):
            super().__init__(shot, stage)
        
        def add_nodes(self):
            load_shot_node = self.create_load_department_layers_node()
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
        def __init__(self, shot: Shot, department_name: str, stage: hou.Node=hou.node('/stage')):
            self.department_name = department_name
            self.import_layout_node = None
            super().__init__(shot, stage)
        
        # Override
        def add_nodes(self):
            self.import_layout_node = self.create_import_layout_node()
            load_shot_node = self.create_load_department_layers_node(self.import_layout_node)
            if (self.department_name != 'lighting'): # Lighting is the only department that needs to see the CFX
                load_shot_node.parm('include_cfx').set(0)
            layer_break_node = self.add_layer_break_node(load_shot_node)

            self.begin_null = layer_break_node.createOutputNode('null', 'BEGIN_' + self.department_name)
            self.my_created_nodes.append(self.begin_null)

            last_department_node = self.add_department_specific_nodes(self.begin_null)

            self.end_null = last_department_node.createOutputNode('null', 'END_' + self.department_name)
            self.my_created_nodes.append(self.end_null)
            self.end_null.setDisplayFlag(True)

            self.create_department_usd_rop_node(self.end_null)
            self.post_add_department_specific_nodes()
            self.post_set_selection()
            self.post_set_view()

        def create_import_layout_node(self):
            import_layout_node = HoudiniNodeUtils.create_node(self.stage, 'accomp_import_layout')
            import_layout_node.parm('import_from').set('auto') # Set the input from to be auto
            self.my_created_nodes.append(import_layout_node)
            return import_layout_node
        
        def create_department_usd_rop_node(self, configure_department_scene_graph: hou.Node):
            # Add the usd rop node/p
            usd_rop_node = configure_department_scene_graph.createOutputNode('usd_rop', 'OUT_' + self.shot.name + '_' + self.department_name)
            usd_rop_node.parm("trange").set(1) # Set the time range to include the entire frame range
            usd_rop_node.parm("lopoutput").set(self.shot.get_shot_usd_path(self.department_name))
            
            self.my_created_nodes.append(usd_rop_node)
            return usd_rop_node
        
        def add_layer_break_node(self, input_node: hou.Node):
            layer_break_node = input_node.createOutputNode('layerbreak')
            layer_break_node.setComment("Keep this node here unless you have a specific reason to delete it.")
            self.my_created_nodes.append(layer_break_node)
            return layer_break_node
        
        def add_department_specific_nodes(self, begin_null: hou.Node) -> hou.Node:
            return begin_null

        def post_add_department_specific_nodes(self):
            pass

        def post_set_selection(self):
            pass

        def post_set_view(self):
            pass
    
    class CameraSceneCreator(DepartmentSceneCreator):
        camera_prim_path = None
        selected_node: hou.Node = None

        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'camera', stage)
            self.camera_prim_path = HoudiniPathUtils.get_camera_prim_path(self.shot)

        def post_set_view(self):
            desktop: hou.Desktop = hou.ui.curDesktop()
            scene_viewer: hou.SceneViewer = desktop.paneTabOfType(hou.paneTabType.SceneViewer)
            viewport: hou.GeometryViewport = scene_viewer.curViewport()
            viewport.setCamera(self.camera_prim_path)
        
        def post_set_selection(self):
            self.selected_node.setSelected(True, clear_all_selected=True)
            self.selected_node.parmTuple('folder2').set((1,))
        
        def add_department_specific_nodes(self, begin_null) -> hou.Node:
            reference_node = self.create_camera_reference_node(begin_null)
            self.my_created_nodes.append(reference_node)
            reference_node.parm('reload').pressButton()
            
            camera_edit_node = self.create_camera_edit_node(reference_node)
            self.my_created_nodes.append(camera_edit_node)
            self.selected_node = camera_edit_node
            
            return camera_edit_node
        
        def create_camera_reference_node(self, input_node: hou.Node):
            # Get the filepath for the camera usd file
            camera_filepath = self.shot.get_camera('RLO')

            # Create reference node
            reference_node: hou.Node = input_node.createOutputNode('reference')

            # Set necessary parms
            reference_node.parm('primpath1').set(self.camera_prim_path)
            reference_node.parm('filepath1').set(camera_filepath)
            reference_node.parm('timeoffset1').set(1000)
            
            return reference_node
        
        def create_camera_edit_node(self, input_node: hou.Node):
            # Create camera node
            camera_edit_node: hou.Node = input_node.createOutputNode('camera')
            
            # Set necessary parms
            camera_edit_node.parm('createprims').set('off')
            camera_edit_node.parm('primpattern').set(self.camera_prim_path)
            camera_edit_node.parm('xn__xformOptransform_51a').set('world')
            camera_edit_node.parm('scale').set(0.01)

            # Turn off unnecessary parms
            camera_edit_node.parm('projection_control').set('none')
            camera_edit_node.parm('focalLength_control').set('none')
            camera_edit_node.parm('aperture').set('none')
            camera_edit_node.parm('horizontalApertureOffset_control').set('none')
            camera_edit_node.parm('verticalApertureOffset_control').set('none')
            camera_edit_node.parm('xn__houdiniguidescale_control_thb').set('none')
            camera_edit_node.parm('xn__houdiniinviewermenu_control_2kb').set('none')
            camera_edit_node.parm('xn__houdinibackgroundimage_control_ypb').set('none')
            camera_edit_node.parm('xn__houdiniforegroundimage_control_ypb').set('none')

            camera_edit_node.parm('xn__shutteropen_control_16a').set('none')
            camera_edit_node.parm('xn__shutterclose_control_o8a').set('none')
            camera_edit_node.parm('focusDistance_control').set('none')
            camera_edit_node.parm('fStop_control').set('none')
            camera_edit_node.parm('exposure_control').set('none')

            # Set node name
            camera_edit_node_num = 1
            result = False
            while result is False:
                try:
                    camera_edit_node.setName('camera_edit' + str(camera_edit_node_num))
                    result = True
                except:
                    camera_edit_node_num += 1
            
            return camera_edit_node
    
    class AnimSceneCreator(DepartmentSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'anim', stage)
        # def post_add_department_specific_nodes(self):
            # add_motion_vectors_node = self.stage.createNode('accomp_add_motion_vectors_to_anim')
            # add_motion_vectors_node.setComment("Please keep this node here, it will make exporting slower but it makes motion blur possible :)")
            # HoudiniNodeUtils.insert_node_after(self.end_null, add_motion_vectors_node)
            # self.my_created_nodes.append(add_motion_vectors_node)
    
    class LightingSceneCreator(DepartmentSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'lighting', stage)
        
        def post_add_department_specific_nodes(self):
            motion_blur_node = self.end_null.createOutputNode('accomp_motion_blur')
            self.my_created_nodes.append(motion_blur_node)
            render_settings_node = motion_blur_node.createOutputNode('hdprmanrenderproperties') # TODO: When you know where these are going to be rendered out, you can automate setting this.
            self.my_created_nodes.append(render_settings_node)
            final_scene_usd_rop_node = self.add_final_scene_usd_rop_node(render_settings_node)
            self.my_created_nodes.append(final_scene_usd_rop_node)

            entire_scene_sublayer = self.create_sublayer_node_to_import_entire_scene()
            self.my_created_nodes.append(entire_scene_sublayer)

            tractor_node = self.create_tractor_node()
            self.my_created_nodes.append(tractor_node)

        def add_final_scene_usd_rop_node(self, input_node: hou.Node):
            usd_rop_node = input_node.createOutputNode('usd_rop', 'OUT_' + self.shot.name)
            usd_rop_node.parm("trange").set(1) # Set the time range to include the entire frame range
            usd_rop_node.parm("lopoutput").set(self.shot.get_shot_usd_path())
            usd_rop_node.parm('striplayerbreaks').set(0) # Turn off layer breaks so that the USD contains all the layers for rendering

            return usd_rop_node
        
        def create_sublayer_node_to_import_entire_scene(self):
            sublayer = HoudiniNodeUtils.create_node(self.stage, 'sublayer')
            sublayer.setName(self.shot.name + '_preview', unique_name=True)
            sublayer.parm('filepath1').set(self.shot.get_shot_usd_path())
            return sublayer
        
        def create_tractor_node(self):
            tractor_node = HoudiniNodeUtils.create_node(self.stage, 'tractor_submit')
            tractor_node.parm('filepath1').set(self.shot.get_shot_usd_path())
            tractor_node.parm('createplayblasts').set(1)
            return tractor_node
        
    
    # As of right now, the CFXSceneCreator just bypasses the layout node by default
    class CFXSceneCreator(DepartmentSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'cfx', stage)
        
        def post_add_department_specific_nodes(self):
            self.import_layout_node.bypass(True)
    
    class FXSceneCreator(DepartmentSceneCreator, ABC):
        pass

    class MainFXSceneCreator(FXSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'fx', stage)

        def post_add_department_specific_nodes(self):
            self.my_created_nodes.extend(HoudiniFXUtils.insert_missing_cached_fx_into_main_fx_file(self.shot))
            
            self.stage.layoutChildren()

    class WorkingFileFXSceneCreator(FXSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage'), fx_name: str=None):
            super().__init__(shot, 'fx', stage)
            self.fx_name = fx_name
            self.object_network = hou.node('/obj')
            self.fx_geo_node = None
            self.animated_geos = {
                'ed': None,
                'letty': None,
                'studentcar': None,
                'vaughn': None
            }
        

        def create_cache_node(self):
            cache_node = self.stage.createNode('cache::2.0')
            cache_node.parm('behavior').set('currentframe')
            cache_node.parm('sample_subframeenable').set(1)
            cache_node.parm('sample_count').set(4)
            return cache_node


        def post_add_department_specific_nodes(self):
            self.import_camera_geo()
            self.import_animation_geo()
            self.fx_geo_node = self.create_fx_geo_node()
            # Color the fx geo node red
            self.fx_geo_node.setColor(hou.Color((1, 0, 0)))
            self.fx_geo_node.parent().setColor(hou.Color((1, 0, 0)))
            self.fx_geo_node.setDisplayFlag(True)
            cache_node = self.create_cache_node()
            self.my_created_nodes.append(cache_node)
            HoudiniNodeUtils.insert_node_after(self.end_null, cache_node)

            self.import_layout()
            if self.fx_name == 'leaves_and_gravel':
                HoudiniFXUtils.LeavesAndGravelUSDGeometryCacheEffectWrapper(self.fx_geo_node).wrap()
            elif self.fx_name == 'background_cop_cars':
                HoudiniFXUtils.BackgroundCopCarsUSDGeometryCacheEffectWrapper(self.fx_geo_node).wrap()
            elif self.fx_name == 'smoke':
                # Bypass the cache node
                cache_node.bypass(True)
                HoudiniFXUtils.USDGeometryCacheEffectWrapper(self.fx_geo_node).wrap()
            else:
                HoudiniFXUtils.USDGeometryCacheEffectWrapper(self.fx_geo_node).wrap()
            self.object_network.layoutChildren()
            
            # Put import nodes into a box
            nodes_to_put_in_box = [node for node in self.object_network.children() if node.name().startswith('import_')]
            box = self.object_network.createNetworkBox()
            box.setComment("Imported Geometry")
            for node in nodes_to_put_in_box:
                box.addNode(node)

        
        def create_fx_geo_node(self):
            fx_geo_node = HoudiniNodeUtils.create_node(self.object_network, 'geo')
            fx_geo_node.setName(self.fx_name, unique_name=True)
            nodes_to_layout = []
            for animated_character in self.animated_geos:
                for char_geo in self.animated_geos[animated_character]:
                    if char_geo == 'packed': # Skip the packed null
                        continue
                    object_merge = fx_geo_node.createNode('object_merge')
                    object_merge.setName(animated_character + '_' + char_geo, unique_name=True)
                    object_merge.parm('objpath1').set(self.animated_geos[animated_character][char_geo].path())
                    nodes_to_layout.append(object_merge)
            

            output_null = fx_geo_node.createNode('null', 'OUT_' + self.fx_name)            
            nodes_to_layout.append(output_null)
            fx_geo_node.layoutChildren(items=nodes_to_layout, vertical_spacing = 0)
            return output_null
        
        def import_animation_geo(self):
            for animated_character in self.animated_geos:
                self.animated_geos[animated_character] = self.import_character_geo(animated_character)

        def import_character_geo(self, character_name):
            """
            Import character geometry into the scene.

            Args:
                character_name (str): The name of the character.

            Returns:
                dict: A dictionary containing the packed and unpacked nulls for the character.
            """
            character_geo_node = HoudiniNodeUtils.create_node(self.object_network, 'geo')
            character_geo_node.setName('import_' + character_name, unique_name=True)
            character_import_node = character_geo_node.createNode('lopimport')
            character_import_node.setName('import_' + character_name, unique_name=True)
            character_import_node.parm('loppath').set(self.load_department_layers_node.path()) # Get the path to the character that's loaded here
            character_import_node.parm('primpattern').set('/scene/anim/' + character_name + '/')
            packed_null = character_import_node.createOutputNode('null', 'OUT_' + character_name)
            unpack_node = character_import_node.createOutputNode('unpackusd', 'unpack_' + character_name)
            unpack_node.parm('output').set(1) # Set output to 'Polygons'
            unpacked_null = unpack_node.createOutputNode('null', 'OUT_' + character_name + '_unpacked')
            character_geo_node.layoutChildren(items=[character_import_node, unpack_node, unpacked_null, packed_null])

            return {
                'packed': packed_null,
                'unpacked': unpacked_null
            }

            
        def import_camera_geo(self):
            camera_geo_node = HoudiniNodeUtils.create_node(self.object_network, 'lopimportcam')
            camera_geo_node.setName('import_camera', unique_name=True)
            camera_geo_node.parm('loppath').set(self.load_department_layers_node.path()) # Get the path to the camera that's loaded here
            camera_geo_node.parm('primpath').set(HoudiniPathUtils.get_camera_prim_path(self.shot))
            return camera_geo_node
        
        def import_layout(self):
            self.exclude_trees = True
            layout_geo_node = self.object_network.createNode('geo')
            layout_geo_node.setName('import_layout', unique_name=True)
            layout_import_node = layout_geo_node.createNode('lopimport')
            layout_import_node.setName('import_layout', unique_name=True)
            layout_import_node.parm('loppath').set(self.load_department_layers_node.path()) # Get the path to the layout that's loaded here
            if self.exclude_trees:
                layout_import_node.parm('primpattern').set('/scene/layout/* - /scene/layout/trees/')
            else:
                layout_import_node.parm('primpattern').set('/scene/layout')
            layout_import_node.parm('timesample').set(0) # Make it so that the node is not time dependent


class HoudiniPathUtils():
    @staticmethod
    def get_fx_usd_cache_folder_path():
        shot_name = HoudiniUtils.get_shot_name()
        if shot_name is None:
            return None
        shot = pipe.server.get_shot(shot_name)
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
    
    @staticmethod
    def get_camera_prim_path(shot: Shot):
        return '/scene/camera/camera_' + shot.get_name()
    
class HoudiniSceneOpenerFactory:
    def __init__(self, shot, department_name):
        self.shot = shot
        self.department_name = department_name
    
    def get_shot_opener(self):
        if self.department_name == 'fx':
            return FXSceneOpener(self.shot)
        else:
            return HoudiniShotOpener(self.shot, self.department_name)
            
class HoudiniShotOpener:
    def __init__(self, shot, department_name):
        self.shot = shot
        self.department_name = department_name
    
    def open_file_path(self, file_path):
        # If the file already exists, go ahead and load it!
        if os.path.isfile(file_path):
            HoudiniUtils.open_file(file_path)
        
        else: # Otherwise create a new file and save it!
            self.create_new_shot_file(file_path)
    
    def create_new_shot_file(self, file_path):
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        hou.hipFile.clear(suppress_save_prompt=True)
        hou.hipFile.save(file_path)
        
        HoudiniUtils.configure_new_shot_file(self.shot, self.department_name)
        
        hou.hipFile.save(file_path)
    
    
    def open_shot(self):
        if self.department_name is None:
            return

        file_path = self.shot.get_shotfile(self.department_name)
        self.open_file_path(file_path)
        
    
class FXSceneOpener(HoudiniShotOpener):
    def __init__(self, shot):
        super().__init__(shot, 'fx')
    
    def open_shot(self):
        # See which subfile the user wants to open, first by prompting the user with the existing files in the working directory
        fx_file_names = ['main'] + HoudiniFXUtils.get_names_of_fx_files_in_working_directory(self.shot)
        fx_subfile_dialog = ListWithFilter("Open FX File for Shot " + self.shot.name, fx_file_names, accept_button_name="Open", cancel_button_name="Create New", list_label="Select the FX file you'd like to open. If you don't see the file you want, click 'Create New' to create a new FX file.", include_filter_field=False)
        
        file_path = None
        if fx_subfile_dialog.exec_():
            selected_fx_file_name = fx_subfile_dialog.get_selected_item()
            if selected_fx_file_name:
                if selected_fx_file_name == 'main':
                    file_path = self.shot.get_shotfile('fx')
                else:
                    file_path = HoudiniFXUtils.get_working_file_path(self.shot, selected_fx_file_name)
        else: # If the user didn't select a file prompt them to create a new one!
            new_fx_file_dialog = ListWithFilter("Create New FX File for Shot " + self.shot.name, HoudiniFXUtils.supported_FX_names, accept_button_name="Create", cancel_button_name="Other", list_label="Select the type of FX file you'd like to create from the known FX types. Otherwise click 'Other' to create a new FX type.", include_filter_field=False)
            if new_fx_file_dialog.exec_():
                selected_fx_file_name = new_fx_file_dialog.get_selected_item()
                if selected_fx_file_name:
                    file_path = HoudiniFXUtils.get_working_file_path(self.shot, selected_fx_file_name)
            else:
                # Prompt the user for the name of the file they want to create
                new_fx_type = hou.ui.readInput(
                    "Enter the name of the new FX file you'd like to create.",
                    title="Create New FX File for shot " + self.shot.name
                    )
                if new_fx_type[0] == 0:
                    new_fx_type_name = new_fx_type[1]
                    new_fx_type_name = new_fx_type_name.replace(' ', '_').lower()
                    if new_fx_type_name == '':
                        print("No file was created.")
                        return
                    file_path = HoudiniFXUtils.get_working_file_path(self.shot, new_fx_type[1])
                else:
                    print("No file was created.")
                    return


        self.open_file_path(file_path)
        


class HoudiniUtils:
    def get_my_path():
        return hou.hipFile.path()
    
    @staticmethod
    def perform_operation_on_houdini_file(filepath: str, save_after_operation: bool, operation: callable, *args, **kwargs):
        try:
            HoudiniUtils.open_file(filepath)
        except AssertionError as e:
            print(e)
            return None
        operation(*args, **kwargs)
        if save_after_operation:
            hou.hipFile.save()
        # else:
        #     hou.hipFile.clear(suppress_save_prompt=True)
    
    @staticmethod
    def perform_operation_on_houdini_files(file_paths: list, save_after_operation: bool, operation: callable, *args, **kwargs):
        for file_path in file_paths:
            HoudiniUtils.perform_operation_on_houdini_file(file_path, save_after_operation, operation, *args, **kwargs)
    
    @staticmethod
    def open_file(file_path):
        assert os.path.exists(file_path), "File does not exist: " + file_path
        hou.hipFile.load(file_path, suppress_save_prompt=True)

    @staticmethod
    def configure_new_shot_file(shot: Shot, department_name: str):
        HoudiniNodeUtils.configure_new_scene(shot, department_name)
        HoudiniUtils.set_frame_range_from_shot(shot)
    
    @staticmethod
    def open_shot_file(shot = None, department_name = None):
        if HoudiniUtils.check_for_unsaved_changes() == 1:
            return
    
        if shot is None:
            shot, department = HoudiniUtils.prompt_user_for_shot_and_department(department_name)
        shot_opener = HoudiniSceneOpenerFactory(shot, department).get_shot_opener()
        shot_opener.open_shot()


    @staticmethod
    def get_shot_name() -> str or None:
        """ Returns the shot name based on the current Houdini session's file path """
        my_path = HoudiniUtils.get_my_path()
        return FilePathUtils.get_shot_name_from_file_path(my_path)
    
    @staticmethod
    def get_department() -> str or None:
        """ Returns the department from a file path """
        return FilePathUtils.get_department_from_file_path(HoudiniUtils.get_my_path())
    
    @staticmethod
    def get_shot_for_file(retrieve_from_shotgrid=False) -> Shot or None:
        shot_name = HoudiniUtils.get_shot_name()
        if shot_name is None:
            return None
        return pipe.server.get_shot(HoudiniUtils.get_shot_name(), retrieve_from_shotgrid=retrieve_from_shotgrid)

    @staticmethod
    def check_for_unsaved_changes():
        """
        Checks if the current Houdini file has unsaved changes.

        Returns:
            int: The user's response to the warning message. 0 for "Continue" (or no unsaved changes), 1 for "Cancel".
        """
        if hou.hipFile.hasUnsavedChanges():
            warning_response = hou.ui.displayMessage(
                "The current file has not been saved. Continue anyway?",
                buttons=("Continue", "Cancel"),
                severity=hou.severityType.ImportantMessage,
                default_choice=1
            )
            return warning_response
        return 0

    @staticmethod
    def prompt_user_for_shot_and_department(selected_department=None):
        """
        Prompts the user to select a shot and department.

        Args:
            selected_department (str, optional): The pre-selected department. Defaults to None.

        Returns:
            tuple: A tuple containing the selected shot and department.

        If the user cancels the shot selection, None is returned for both shot and department.
        If no department is provided, the user is prompted to select a department.

        """
        shot = HoudiniUtils.prompt_user_for_shot()
        if shot is None:
            return None, None
        if selected_department is None:
            user_selected_department = HoudiniUtils.prompt_user_for_subfile_type()
        else:
            user_selected_department = selected_department
        return shot, user_selected_department

    @staticmethod
    def prompt_user_for_shot():
        shot_names = sorted(pipe.server.get_shot_list())
        dialog = ListWithFilter("Open Shot File", shot_names)

        if dialog.exec_():
            selected_shot_name = dialog.get_selected_item()
            if selected_shot_name:
                shot = pipe.server.get_shot(selected_shot_name, retrieve_from_shotgrid=True)
                return shot
        return None
        
    @staticmethod
    def prompt_user_for_subfile_type() -> str or None:
        subfile_types = FilePathUtils.subfile_types
        dialog = ListWithFilter("Open Shot Subfile", subfile_types, list_label="Select the Shot Subfile that you'd like to open.")
        if dialog.exec_():
            selected_subfile_type = dialog.get_selected_item()
            return selected_subfile_type
        return None

    @staticmethod
    def set_frame_range_from_shot(shot: Shot, global_start_frame=1001, handle_frames=5):
        if shot.cut_in is None or shot.cut_out is None:
            shot = pipe.server.get_shot(shot.name, retrieve_from_shotgrid=True)
        handle_start, shot_start, shot_end, handle_end = shot.get_shot_frames(global_start_frame=global_start_frame, handle_frames=handle_frames)
        hou.playbar.setFrameRange(handle_start, handle_end)
        hou.playbar.setPlaybackRange(shot_start, shot_end)
    
    @staticmethod
    def hyper_rop():
        # This is intended to disconnect things from above the begin null, rop, and then reconnect them to the begin null. For some reason this is a lot faster and the results seem to be *mostly* the same
        # Get the BEGIN_ node using the custom helper function
        begin_null = HoudiniNodeUtils.find_first_node_name_starts_with(hou.node('/stage'), 'BEGIN_')

        # Get the usd_rop node using the custom helper function
        rop_node = HoudiniNodeUtils.find_first_node_of_type(hou.node('/stage'), 'usd_rop')

        # Check if the BEGIN_ node exists and has an input
        if begin_null and begin_null.inputs():
            # Store the connected node for reconnection later
            connected_node = begin_null.inputs()[0]
            # Disconnect the connected node from the BEGIN_ node
            begin_null.setInput(0, None)
        else:
            raise Exception('No "BEGIN_" null in scene!')

        # Check if the USD ROP node exists
        if rop_node:
            # Trigger the 'Save to Disk' action on the USD ROP node
            rop_node.parm('execute').pressButton()
        else:
            raise Exception('No ROP node in scene!')

        # Reconnect the BEGIN_ node with the previously connected node
        assert begin_null and connected_node, "BEGIN_ node and connected node must be defined."
        begin_null.setInput(0, connected_node)
    
    @staticmethod
    def render_flipbook_to_video(output_directory, filename_base, frame_range=None, resolution=(1920, 1080),
                                video_format='mov', codec='prores', profile='standard'):
        """
        Renders a flipbook in Houdini and saves it as a video file (MP4 or MOV), overwriting if the file already exists.

        Parameters:
        - output_directory: The directory where the flipbook images and video will be saved.
        - filename_base: The base name for the output files.
        - frame_range: A tuple specifying the start and end frames for the flipbook.
        - resolution: The resolution of the flipbook images.
        - video_format: The format of the video file ('mp4' or 'mov').
        - codec: The codec to use for the video ('libx264' for MP4, 'prores' for MOV).
        - profile: The profile to use with the codec, if applicable (e.g., 'proxy' for ProRes).
        """

        # Ensure the output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Set up flipbook settings
        scene = toolutils.sceneViewer()
        settings = scene.flipbookSettings()
        if frame_range is not None:
            settings.frameRange(frame_range)
        settings.useResolution(True)
        settings.resolution(resolution)
        
        # Specify the output path for the JPG sequence
        output_path = os.path.join(output_directory, f'{filename_base}.$F4.jpg')
        settings.output(output_path)

        # Render the flipbook
        scene.flipbook(None, settings)

        # Construct the video file path and check if it exists, remove if it does
        video_output_path = os.path.join(output_directory, f'{filename_base}.{video_format}')
        if os.path.exists(video_output_path):
            os.remove(video_output_path)

        # Prepare the FFmpeg command based on the specified format and codec
        jpg_sequence = os.path.join(output_directory, f'{filename_base}.%04d.jpg')
        ffmpeg_cmd = f'ffmpeg -framerate 24 -i "{jpg_sequence}" -c:v {codec} '
        
        if codec == 'prores' and profile:
            ffmpeg_cmd += f'-profile:v {profile} '
        elif codec == 'libx264':
            ffmpeg_cmd += '-pix_fmt yuv420p '
        
        ffmpeg_cmd += f'"{video_output_path}"'
        
        # Execute the FFmpeg command to create the video file
        subprocess.call(ffmpeg_cmd, shell=True)

        # Clean up the JPG images
        for frame_number in range(frame_range[0], frame_range[1] + 1):
            jpg_file_path = os.path.join(output_directory, f'{filename_base}.{frame_number:04d}.jpg')
            if os.path.exists(jpg_file_path):
                os.remove(jpg_file_path)

        print(f'Flipbook rendered and saved as {video_output_path}')






class HoudiniFileVersionManager(DCCVersionManager):
    def get_my_path(self):
        file_path = HoudiniUtils.get_my_path()
        if 'untitled' in file_path.lower(): # By default, if you haven't saved anything yet, the file path will be 'untitled'
            return None # The DCCVersionManager will throw an error if you return None here
        return file_path

    def open_file(self):
        HoudiniUtils.open_file(self.vm.get_main_path())
    
    def check_for_unsaved_changes_and_inform_user(self):
        return HoudiniUtils.check_for_unsaved_changes() == 1