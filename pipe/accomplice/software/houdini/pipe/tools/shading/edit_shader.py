import hou
import os
import pxr
import random
import pipe
from pipe.shared.object import *
from pathlib import *


MATLIB_NAME = "Material_Library"

class EditShader():

    #Called on node placement
    def __init__(self):

        self.asset = None
        self.materials = {}
        self.materialsAsset = None
        self.nodes_path = None
 
    def matLib(self):
        return hou.node('./' + MATLIB_NAME)

    #Called when asset is chosen on HDA
    def set_asset(self, asset_name):

        if asset_name == None:
            self.asset = None
            self.materials = {}
            self.materialsAsset = None
            self.nodes_path = None
            return

        self.asset = pipe.server.get_asset(asset_name)
        self.nodes_path = Path(self.asset.path) / 'mats' / 'metadata' / 'nodes.uti'

        if self.nodes_path.is_file():
            hou.node('.').parm('load_usd').hide(False)

        try:
            with open(self.asset.path + '/mats/metadata/' + self.asset.name + '_meta.json', 'r') as f:
                print('successfully opened file')
                self.materialsAsset = MaterialsAsset.from_string(f.read())

                for material in self.materialsAsset.textureSets:
                    self.materials[material] = {}

        except FileNotFoundError:
            print('this file does not exist yet. Export from Substance Painter first')

    #Load button, loads uti file stored on disk
    def load_materials(self, kwargs):
        print("loading")

        #clear the slate
        self.clear_materials()

        self.matLib().loadItemsFromFile(str(self.nodes_path))
        self.update_UI()

    #publishes uti of node networks and materials usd
    def publish_materials(self):
        print('publishing')

        for material in self.materials.keys():
            controls = self.matLib().node('controls_' + material.name)

            #evaluate parameters in place to preserve values
            for parm in controls.allParms():
                #bypass unneeded parm
                if parm.name() != 'outputnum':

                    val = parm.eval()
                    print(val)
                    parm.deleteAllKeyframes()
                    parm.set(val)


        self.matLib().saveItemsToFile(self.matLib().allItems(), str(self.nodes_path))

        rop = hou.node('./usd_out')

        path = Path(self.asset.path) / 'mats' / 'mats.usd'

        rop.parm('lopoutput').set(str(path))
        rop.parm('execute').pressButton()

    #create networks from scratch
    def create_materials(self):
        print("creating network")

        #clear the slate
        self.clear_materials()

        #create materials for each texture set
        for material in self.materials:
            self.create_material(material)

        self.update_UI()

    #These sets of methods load and initialize material networks from pre defined prototypes
    def create_material(self, mat):
        matType = MaterialType(mat.matType)

        if matType == MaterialType.BASIC:
            print('creating basic')
            self.create_basic(mat)

        if matType == MaterialType.METAL:
            print('creating metal')
            self.create_metal(mat)

        if matType == MaterialType.GLASS:
            print('creating glass')
            self.create_glass(mat)

        if matType == MaterialType.CLOTH:
            print('creating cloth')
            self.create_cloth(mat)

        if matType == MaterialType.SKIN:
            print('creating skin')
            self.create_skin(mat)

        self.matLib().layoutChildren()

        self.load_textures(mat)

    def create_basic(self, mat):
        before = self.matLib().allItems()
        self.matLib().loadItemsFromFile('/groups/accomplice/shading/DEF/BASIC_MAT.uti')
        after = self.matLib().allItems()

        added = self.get_added_nodes(before, after)

        self.rename_nodes(added, mat)
        self.set_node_references(mat)

    def create_metal(self, mat):
        before = self.matLib().allItems()
        self.matLib().loadItemsFromFile('/groups/accomplice/shading/DEF/BASIC_MAT.uti')
        after = self.matLib().allItems()

        added = self.get_added_nodes(before, after)

        self.rename_nodes(added, mat)
        self.set_node_references(mat)

    def create_glass(self, mat):
        before = self.matLib().allItems()
        self.matLib().loadItemsFromFile('/groups/accomplice/shading/DEF/GLASS_MAT.uti')
        after = self.matLib().allItems()

        added = self.get_added_nodes(before, after)

        self.rename_nodes(added, mat)
        self.set_node_references(mat)

    def create_cloth(self, mat):
        before = self.matLib().allItems()
        self.matLib().loadItemsFromFile('/groups/accomplice/shading/DEF/CLOTH_MAT.uti')
        after = self.matLib().allItems()

        added = self.get_added_nodes(before, after)

        self.rename_nodes(added, mat)
        self.set_node_references(mat)

    def create_skin(self, mat):
        before = self.matLib().allItems()
        self.matLib().loadItemsFromFile('/groups/accomplice/shading/DEF/SKIN_MAT.uti')
        after = self.matLib().allItems()

        added = self.get_added_nodes(before, after)

        self.rename_nodes(added, mat)
        self.set_node_references(mat)

    #set necessary references for applying textures later on
    def set_node_references(self, mat):
        
        self.materials[mat]['DiffuseColor'] = self.matLib().node('diffuse_color_' + mat.name)
        self.materials[mat]['SpecularFaceColor'] = self.matLib().node('spec_face_color_' + mat.name)
        self.materials[mat]['SpecularRoughness'] = self.matLib().node('spec_roughness_' + mat.name)
        self.materials[mat]['Normal'] = self.matLib().node('normal_map_' + mat.name)
        self.materials[mat]['Presence'] = self.matLib().node('presence_' + mat.name)
        self.materials[mat]['Displacement'] = self.matLib().node('displacement_' + mat.name)

    #put the texture path into each texture node
    def load_textures(self, material):

        nodes = self.materials[material]

        channels = ['DiffuseColor', 'SpecularFaceColor', 'SpecularRoughness', 'Normal', 'Presence', 'Displacement']
        tex_folder_path = Path(self.asset.path) / 'mats' / 'textures' / 'RMAN'

        for channel in channels:

            print(nodes[channel].parm('filename'))
            channel_path = ""

            if material.hasUDIMs:
                channel_path = str(tex_folder_path) + '/' + material.name + '_' + channel + '_srgbtex_acescg.<UDIM>.png.tex'
            else:
                channel_path = str(tex_folder_path) + '/' + material.name + '_' + channel + '_srgbtex_acescg.png.tex'
            
            #hacky fix for roughness. ugh... ignore me while I poop all over the place
            if channel == 'SpecularRoughness' or channel == 'Normal':
                print('spec')
                channel_path = channel_path.replace('srgbtex', 'data')

            nodes[channel].parm('filename').set(str(channel_path))

            #setup previs color shader
            if channel == 'DiffuseColor':
                channel_path = ""

                if material.hasUDIMs:
                    channel_path = str(tex_folder_path) + '/' + material.name + '_' + channel + '.<UDIM>.png'
                else:
                    channel_path = str(tex_folder_path) + '/' + material.name + '_' + channel + '.png'
                
                self.matLib().node('preview_diffuse_color_' + material.name).parm('file').set(channel_path)
            
    #assign each material to its corresponding named primitive
    def assign_materials(self, value):
        print("assigning")

        if value == 1:

            component_mat = hou.node('./' + COMPONENT_MAT_NAME)
            component_mat.parm('nummaterials').set(len(self.materials) * 2)

            #geo subsets
            input = hou.node('./INPUT_GEO')
            geo = input.stage()

            count = 1
            print(list(self.materials.keys()))

            for material in list(self.materials.keys()):
                
                component_mat.parm('primpattern' + str(count)).set('/ASSET/geo/render/' + material.name)
                component_mat.parm('matspecpath' + str(count)).set('/ASSET' + material.materialPath)

                component_mat.parm('primpattern' + str(count+1)).set('/ASSET/geo/proxy/' + material.name)
                component_mat.parm('matspecpath' + str(count+1)).set('/ASSET' + material.materialPath)
                
                count += 2

            hou.node('switch2').parm('input').set(0)
        else:
            hou.node('switch2').parm('input').set(1)
    
    def clear_materials(self):
        
            for child in self.matLib().allItems():
                if child != None:
                    child.destroy()

    #utility to keep track of the latest nodes added
    def get_added_nodes(self, list1, list2):
        return list(set(list2) - set(list1))

    #translates specified parameters to stage layer
    def create_parm_group(self, material, group):

        folder = hou.FolderParmTemplate(material.name + '_folder', material.name, folder_type=hou.folderType.Simple)

        if material.isPxr:
            print('is pxr')
            controls = self.matLib().node('controls_' + material.name)

            for parm in controls.allParms():
                #bypass unneeded parm
                if parm.name() != 'outputnum':

                    new_name = material.name + '_' + parm.name()
                    out_parm = hou.FloatParmTemplate(new_name, parm.description(), 1, default_value=[parm.eval()])
                    out_parm.setMinValue(0)
                    out_parm.setMaxValue(1)

                    folder.addParmTemplate(out_parm)

                    parm.setExpression('ch(\"../../' + new_name + '\")')
                    hou.node('.').setParmTemplateGroup(group)
            
        group.appendToFolder(('Materials'), folder)

    def update_UI(self):
        print('updating')
        hou.node('.').removeSpareParms()
        
        group = hou.node('.').parmTemplateGroup()

        for material in self.materials:
            self.create_parm_group(material, group)
        
        hou.node('.').setParmTemplateGroup(group)

    #renames a material template
    def rename_nodes(self, added, mat):
        for node in added:
            new_name = node.name().replace('MATERIAL', mat.name)
            node.setName(new_name)

        box = self.matLib().item(mat.name +  '_box')
        box.setComment(mat.name)
        box.setColor(random_color())

#randomly defines a hou.Color()
def random_color():
    return hou.Color((random.uniform(0,1), random.uniform(0,1), random.uniform(0,1)))



