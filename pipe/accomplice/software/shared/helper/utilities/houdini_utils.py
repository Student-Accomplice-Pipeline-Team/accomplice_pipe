import hou
import os
from pathlib import Path
import pipe
from ...object import Shot
from .file_path_utils import FilePathUtils
from abc import ABC, abstractmethod
from .ui_utils import ListWithFilter
from pipe.shared.helper.utilities.dcc_version_manager import DCCVersionManager


class HoudiniFXUtils():
    supported_FX_names = ['sparks', 'smoke', 'money', 'skid_marks']
    FX_PREFIX = "/scene/fx"
    
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
    def create_sublayer_nodes_for_cached_fx(shot: Shot):
        cached_fx_paths = HoudiniFXUtils.get_paths_to_cached_fx(shot)
        sublayer_nodes = []
        for cached_fx_path in cached_fx_paths:
            sublayer_node = HoudiniNodeUtils.create_node(hou.node('/stage'), 'sublayer')
            sublayer_node.parm('filepath1').set(cached_fx_path)
            sublayer_nodes.append(sublayer_node)
        return sublayer_nodes
    
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
                materials_node = HoudiniNodeUtils.create_node(self.effect_import_node.parent(), self.effect_name + "_material")
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

            # Create a reference node that references the usd file
            # reference_node = HoudiniNodeUtils.create_node(usd_rop_node.parent(), 'reference')
            # reference_node.setName(self.effect_name + "_reference", unique_name=True)
            # reference_node.parm('filepath1').set(usd_path)
            # reference_node.parm('primpath1').set(HoudiniFXUtils.FX_PREFIX)
            # reference_node.setDisplayFlag(True)
            # auxiliary_nodes.append(reference_node)
            
            # Layout only the associated nodes
            self.effect_import_node.parent().layoutChildren()

            # Create a network box and add the nodes to it
            # box = self.effect_import_node.parent().createNetworkBox()
            # box.setComment("Configure " + self.effect_name)
            # for node in auxiliary_nodes:
            #     box.addNode(node)

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
            self.configure_sop_import_lop(sop_import_lop)
            return sop_import_lop

        def create_sop_import_lop(self):
            """Creates SOP Import node from the first node in selection."""
            lop_node = HoudiniNodeUtils.create_node(hou.node('/stage'), 'sopimport')
            lop_node = HoudiniNodeUtils.insert_node_between_two_nodes(self.fx_start_null, self.fx_end_null, lop_node)
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
        'skid_marks_material': 'accomp_skid_marks_material',
    }

    @staticmethod
    def find_first_node_of_type(parent, node_type):

        # Iterate through all nodes in the stage context
        for node in parent.allSubChildren():
            # Check if the node is of the specified type
            if node.type().name() == node_type:
                return node

        # Return None if no node of the specified type is found
        return None
    
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
        nodes_of_type = [node for node in parent_node.allSubChildren() if node.type().name() == node_type]

        return nodes_of_type

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
            super().__init__(shot, stage)
        
        # Override
        def add_nodes(self):
            import_layout_node = self.create_import_layout_node()
            load_shot_node = self.create_load_department_layers_node(import_layout_node)
            layer_break_node = self.add_layer_break_node(load_shot_node)

            begin_null = layer_break_node.createOutputNode('null', 'BEGIN_' + self.department_name)
            self.my_created_nodes.append(begin_null)


            end_null = begin_null.createOutputNode('null', 'END_' + self.department_name)
            self.my_created_nodes.append(end_null)
            end_null.setDisplayFlag(True)

            self.restructure_scene_graph_node = self.add_restructure_scene_graph_node(end_null)
            self.restructure_scene_graph_node.bypass(1)
            self.create_department_usd_rop_node(self.restructure_scene_graph_node)
            self.post_add_department_specific_nodes()

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
        
        def add_restructure_scene_graph_node(self, input_node: hou.Node):
            restructure_scene_graph_node = input_node.createOutputNode('restructurescenegraph')
            restructure_scene_graph_node.parm('flatteninput').set(0)
            restructure_scene_graph_node.setComment("This node can help you put your work into the proper location in the scene graph. Simply adjust the 'primitives' parameter to include the prims you want to move. If you don't do this, your scene will probably still work. If you do this and it breaks, you can probably ignore this node. Reach out to a pipeline technician if you have any questions.")

            # Set the primpattern to include everything that's not a decendant of /scene
            restructure_scene_graph_node.parm('primpattern').set('')
            restructure_scene_graph_node.parm('primnewparent').set('/scene/' + self.department_name)
            self.my_created_nodes.append(restructure_scene_graph_node)
            return restructure_scene_graph_node
        
        def post_add_department_specific_nodes(self):
            pass
    
    class LightingSceneCreator(DepartmentSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'lighting', stage)
        
        def post_add_department_specific_nodes(self):
            motion_blur_node = self.restructure_scene_graph_node.createOutputNode('accomp_motion_blur')
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
            sublayer.setName(self.shot.name + '_preview')
            sublayer.parm('filepath1').set(self.shot.get_shot_usd_path())
            return sublayer
        
        def create_tractor_node(self):
            tractor_node = HoudiniNodeUtils.create_node(self.stage, 'tractor_submit')
            tractor_node.parm('filepath1').set(self.shot.get_shot_usd_path())
            tractor_node.parm('createplayblasts').set(1)
            return tractor_node
        
    
    class FXSceneCreator(DepartmentSceneCreator, ABC):
        pass

    class MainFXSceneCreator(FXSceneCreator):
        def __init__(self, shot: Shot, stage: hou.Node=hou.node('/stage')):
            super().__init__(shot, 'fx', stage)

        def post_add_department_specific_nodes(self):
            sublayer_nodes = HoudiniFXUtils.create_sublayer_nodes_for_cached_fx(self.shot)
            begin_null, end_null = HoudiniFXUtils.get_fx_range_nulls()
            last_node = begin_null
            for sublayer_node in sublayer_nodes:
                last_node = HoudiniNodeUtils.insert_node_between_two_nodes(last_node, end_null, sublayer_node)
                self.my_created_nodes.append(sublayer_node)
            
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

        def post_add_department_specific_nodes(self):
            self.import_camera_geo()
            self.import_animation_geo()
            self.fx_geo_node = self.create_fx_geo_node()
            # Color the fx geo node red
            self.fx_geo_node.setColor(hou.Color((1, 0, 0)))
            self.fx_geo_node.parent().setColor(hou.Color((1, 0, 0)))
            self.fx_geo_node.setDisplayFlag(True)

            self.import_layout()
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
            fx_geo_node.setName(self.fx_name)
            nodes_to_layout = []
            for animated_character in self.animated_geos:
                for char_geo in self.animated_geos[animated_character]:
                    if char_geo == 'packed': # Skip the packed null
                        continue
                    object_merge = fx_geo_node.createNode('object_merge')
                    object_merge.setName(animated_character + '_' + char_geo)
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
            character_geo_node.setName('import_' + character_name)
            character_import_node = character_geo_node.createNode('lopimport')
            character_import_node.setName('import_' + character_name)
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
            camera_geo_node.setName('import_camera')
            camera_geo_node.parm('loppath').set(self.load_department_layers_node.path()) # Get the path to the camera that's loaded here
            camera_geo_node.parm('primpath').set('/scene/camera/camera_' + self.shot.get_name())
            return camera_geo_node
        
        def import_layout(self):
            self.exclude_trees = True
            layout_geo_node = self.object_network.createNode('geo')
            layout_geo_node.setName('import_layout')
            layout_import_node = layout_geo_node.createNode('lopimport')
            layout_import_node.setName('import_layout')
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
        handle_start, shot_start, shot_end, handle_end = shot.get_shot_frames(global_start_frame=global_start_frame, handle_frames=handle_frames)
        hou.playbar.setFrameRange(handle_start, handle_end)
        hou.playbar.setPlaybackRange(shot_start, shot_end)

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