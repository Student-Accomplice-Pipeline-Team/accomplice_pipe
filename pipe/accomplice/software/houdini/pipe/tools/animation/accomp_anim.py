""" This file contains the code for the accomp_anim HDA """

# Imports
import hou
import os, functools
import glob
from pipe.shared.object import Asset
from pipe.shared.helper.utilities.houdini_utils import HoudiniPathUtils
import pipe

# Constants
ANIM_SUBDIRECTORY = 'anim'
EXTENSION = '.usd'

# Functions
class AnimationImporter():

    def __init__(self):
        print("IMPORTING ANIMATION")
        self.shot = self.get_shot()

    def get_shot(self):
        shot_name = HoudiniPathUtils.get_shot_name()
        shot = pipe.server.get_shot(shot_name)
        return shot

    def get_character_options_list(self):
        self.shot = pipe.server.get_shot(HoudiniPathUtils.get_shot_name())
        print('This is the shot name!', self.shot.name)
        display_list = []

        # Check if the current directory has an anim folder
        anim_dir = self.shot.get_shotfile_folder('anim')

        if not os.path.isdir(anim_dir): # Error check
            hou.ui.displayMessage("There doesn't seem to be an anim folder in the context of this file. Contact pipe engineer.")
            return []

        path_to_check = os.path.join(anim_dir, '**', '*' + EXTENSION)
        for file in glob.iglob(path_to_check, recursive=True): # For each file in the anim directory
            if not 'anim_backup' in file:
                # Get the file name, not the full path
                file_name = os.path.basename(file)
                display_list.append(file_name)

        return display_list

    def is_character(self, name: str) -> bool:
        lower_name = name.lower()
        return lower_name in ['letty', 'ed', 'vaughn']

    def get_anim_name(self, node):
        return node.parm('./anim_name').eval()

    def get_asset_name(self, node):
        return node.parm('./asset_name').eval()

    def get_anim_description(self, node):
        return node.parm('./anim_descr').eval()

    # Called when a new character/object name is selected
    def animation_name_update(self, node):
        anim_path = node.parm('./anim_filename').eval() # Get path to file
        print("anim path: ", anim_path)

        anim_name = (anim_path.split('/')[-1])[:-len(EXTENSION)] # Get just the name of the file, excluding extension
        underscore_location = anim_name.find('_')
        asset_name = None
        if underscore_location != -1:
            anim_description = anim_name[underscore_location+1:] # The anim description is everything after the underscore
            asset_name = anim_name[:underscore_location] # The asset name is everything before the underscore
        else:
            asset_name = anim_name
        print("anim name ", anim_name)
        print("asset name: ", asset_name)

        node.parm('./anim_name').set(anim_name)
        node.parm('./asset_name').set(asset_name)
        node.parm('./anim_descr').set(anim_description)

        node.allowEditingOfContents()
        self.set_anim_type(node)
        self.character_material_update(node)

    def get_path_to_materials(self, node):
        asset_name = get_asset_name(node)
        asset_dir = None # TODO: get asset dir from server!
        if asset_dir is None:
            return None
        return os.path.join(asset_dir, "materials")

    def character_material_update(self, node):
        mat_sublayer = node.node('materials')
        path_to_materials = self.get_path_to_materials(node)
        if path_to_materials is None:
            hou.ui.displayMessage("Could not find asset's material folder. Alembic naming may not match. Please manually pull in the material folder to reference in the materials node within.")
        else:
            material_file = os.path.join(path_to_materials, get_asset_name(node) + "_shader.usda")
            mat_sublayer.parm('filepath1').set(material_file)

        mat = node.node('assign_material')
        mat.parm('nummaterials').set(1)
        mat.parm('primpattern1').set('/anim/`chs("../asset_name")`/geo')
        mat.parm('matspecpath1').set('/anim/`chs("../asset_name")`/materials/`chs("../asset_name")`_shader')

    def set_anim_type(self, node):
        anim_type = node.parm('anim_type')
        asset_name = get_asset_name(node)
        fx_enabled = node.parm('fx_enabled')
        if is_character(asset_name):
            anim_type.set('human')
            fx_enabled.set(1)
        else:
            anim_type.set('object')
            fx_enabled.set(0)

    def prune(self, node):
        # Make prim path list
        primive_paths = []
        if (node.parm('hidetemphair').eval() == 1):
            if (node.parm('anim_type').eval() == 'human'):
                primive_paths.append('/anim/`chs("../asset_name")`/geo/temp_hair')
                
        if (node.parm('hidetempcloth').eval() == 1) and (node.parm('anim_type').eval() == 'human'):
            primive_paths.append('/anim/`chs("../asset_name")`/geo/temp_clothing')
            
        if (node.parm('hidefxgeo').eval() == 1) and (node.parm('fx_enabled').eval() == 1):
            primive_paths.append('/anim/`chs("../asset_name")`/geo/fx')
        
        # Set prim path in the prune node
        prune = node.node('display_settings_prune')
        prune.parm('num_rules').set(len(primive_paths))

        for i, primitive_path in enumerate(primive_paths, start=1):
            parameter_name = f'primpattern{i}'
            prune.parm(parameter_name).set(primitive_path)