import hou
import os
import pxr
import random
import pipe
from pipe.shared.object import *
from pathlib import *


MATLIB_NAME = "Material_Library"
COMPONENT_MAT_NAME = "Component_Material"

class EditShader():

    #Called on node placement
    def __init__(self):

        self.asset = None
        self.materials = {}
        self.materialVariant = None
        self.geo_variant_name = None
        self.texturesPath = None
        self.nodes_path = None
 
    def matLib(self):
        return hou.node('./' + MATLIB_NAME)

    #Called when asset is chosen on HDA
    def set_asset(self, asset_name, geo_variant_name, mat_var_name):

        if asset_name == None:
            self.asset = None

            self.materialVariant = None
            self.nodes_path = None
            return
        
        self.materials = {}

        self.asset = pipe.server.get_asset(asset_name)
        
        metadata = self.asset.get_metadata()

        self.materialVariant = metadata.hierarchy[geo_variant_name][mat_var_name]
        self.geo_variant_name = geo_variant_name
        self.texturesPath = self.asset.get_textures_path(geo_variant_name, mat_var_name)
        print(self.texturesPath)

        for _, material in self.materialVariant.materials.items():
                    self.materials[material] = {}

        #print(self.materials.keys())


        #self.nodes_path = Path(self.asset.path) / 'maps' / 'metadata' / 'nodes.uti'

        #if self.nodes_path.is_file():
        #    hou.node('.').parm('load_usd').hide(False)

    #Load button, loads uti file stored on disk
    #####NO LONGER USED########
    def load_materials(self, kwargs):
        print("loading")

        #clear the slate
        self.clear_materials()

        self.matLib().loadItemsFromFile(str(self.nodes_path))
        self.update_UI()

    #publishes uti of node networks and materials usd
    def publish_materials(self):
        print('publishing')

        '''for material in self.materials.keys():
            controls = self.matLib().node('controls_' + material.name)

            #evaluate parameters in place to preserve values
            for parm in controls.allParms():
                #bypass unneeded parm
                if parm.name() != 'outputnum':

                    val = parm.eval()
                    print(val)
                    parm.deleteAllKeyframes()
                    parm.set(val)


        self.matLib().saveItemsToFile(self.matLib().allItems(), str(self.nodes_path))'''

        rop = hou.node('./usd_out')

        path = Path(self.asset.path) / 'mtl.usd'

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
            print(mat.name)
            self.create_basic(mat)

        if matType == MaterialType.METAL:
            print('creating metal')
            self.create_metal(mat)

        if matType == MaterialType.GLASS:
            print(mat.name)
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
        self.matLib().loadItemsFromFile('/groups/accomplice/shading/DEF/METAL_MAT.uti')
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
        
        self.materials[mat]['BaseColor'] = self.matLib().node('preview_diffuse_color_' + mat.name)
        self.materials[mat]['Metallic'] = self.matLib().node('preview_metallic_' + mat.name)
        self.materials[mat]['Roughness'] = self.matLib().node('preview_roughness_' + mat.name)

    #put the texture path into each texture node
    def load_textures(self, material):

        nodes = self.materials[material]

        #Load Renderman Maps
        channels = {'DiffuseColor' : '', 'SpecularFaceColor' : '', 'SpecularRoughness' : '', 'Normal' : '', 'Presence' : '', 'Displacement' : ''}
        tex_folder_path = Path(self.texturesPath + '/')
        files = tex_folder_path.glob('*_' + material.name + '_*.1001.*')
        #print(list(files))
        #print(next(files))

        for file in files:
            path = str(file).replace('1001', '<UDIM>')
            #print(os.path.basename(path))
            if 'DiffuseColor' in path:
                channels['DiffuseColor'] = path
            if 'SpecularFaceColor' in path:
                channels['SpecularFaceColor'] = path
            if 'SpecularRoughness' in path:
                channels['SpecularRoughness'] = path
            if 'Normal' in path:
                channels['Normal'] = path
            if 'Presence' in path:
                channels['Presence'] = path
            if 'Displacement' in path:
                channels['Displacement'] = path
        print('CHANNELS')

        for channel in channels:
            print(os.path.basename(str(channels[channel])))
            if channel != 'Normal':
                nodes[channel].parm('filename').set(channels[channel])
            else:
                nodes[channel].parm('b2r_texture').set(channels[channel])

        #Load Preview Maps
        channels = {'BaseColor' : '', 'Metallic' : '', 'Roughness' : ''}
        tex_folder_path = Path(self.texturesPath + '/PBRMR/')

        files = tex_folder_path.glob('*_' + material.name + '_*.1001.png')
        #print(next(files))

        for file in files:
            #print(file)
            path = str(file).replace('1001', '<UDIM>')
            if 'BaseColor' in path:
                channels['BaseColor'] = path
            if 'Metallic' in path:
                channels['Metallic'] = path
            if 'Roughness' in path:
                channels['Roughness'] = path

        for channel in channels:

            nodes[channel].parm('file').set(channels[channel])
        
            
            #setup previs roughness texture
            if channel == 'SpecularRoughness':
                
                self.matLib().node('preview_roughness_' + material.name).parm('file').set(channels[channel])

    #assign each material to its corresponding named primitive
    def assign_materials(self, value):
        print("assigning")

        if value == 1:

            component_mat = hou.node('./' + COMPONENT_MAT_NAME)
            component_mat.parm('nummaterials').set(len(self.materials) * 2)

            if self.materialVariant != None:
                component_mat.parm('variantname').set(self.materialVariant.name)

            #geo subsets
            input = hou.node('./INPUT_GEO')
            geo = input.stage()

            count = 1
            #print(list(self.materials.keys()))

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

        folder = hou.FolderParmTemplate(material.name + '_folder', material.name, folder_type=hou.folderType.Collapsible)

        if material.isPxr:
            #print('is pxr')
            controls = self.matLib().node('controls_' + material.name)

            hasIOR = False
            hasSubSurfCol = False
            hasFuzzCol = False
            hasExtCoeff = False
    
            for parm in controls.allParms():
                #bypass unneeded parm
                if parm.name() != 'outputnum':

                    if 'iorCol' in parm.name():
                        if not hasIOR:
                            new_name = material.name + '_iorCol'

                            out_parm = hou.FloatParmTemplate(new_name, parm.description(), 3,
                                                            default_value=[controls.evalParm('iorColr'),controls.evalParm('iorColg'),controls.evalParm('iorColb')],
                                                            look=hou.parmLook.ColorSquare, 
                                                            naming_scheme=hou.parmNamingScheme.RGBA)
                            out_parm.setMinValue(0)
                            out_parm.setMaxValue(2)
                            hasIOR = True
                            parm.setExpression('ch(\"../../' + new_name + 'r\")')
                            folder.addParmTemplate(out_parm)
                        else:
    
                            new_name = material.name + '_iorCol' + parm.name().split('iorCol')[1]
                            parm.setExpression('ch(\"../../' + new_name + '\")')
                        
                    elif 'ssc' in parm.name():
                        
                        if not hasSubSurfCol:
                            
                            new_name = material.name + '_ssc'
                            print(new_name)
                            out_parm = hou.FloatParmTemplate(new_name, parm.description(), 3,
                                                            default_value=[controls.evalParm('sscr'),controls.evalParm('sscg'),controls.evalParm('sscb')],
                                                            look=hou.parmLook.ColorSquare, 
                                                            naming_scheme=hou.parmNamingScheme.RGBA)
                            out_parm.setMinValue(0)
                            out_parm.setMaxValue(2)
                            hasSubSurfCol = True
                            parm.setExpression('ch(\"../../' + new_name + 'r\")')
                            folder.addParmTemplate(out_parm)
                            
                        else:
                            new_name = material.name + '_ssc' + parm.name().split('ssc')[1]
                            parm.setExpression('ch(\"../../' + new_name + '\")')
                    
                    elif 'extcoeff' in parm.name():
                        
                        if not hasExtCoeff:
                            
                            new_name = material.name + '_extcoeff'
                            print(new_name)
                            out_parm = hou.FloatParmTemplate(new_name, parm.description(), 3,
                                                            default_value=[controls.evalParm('extcoeffr'),controls.evalParm('extcoeffg'),controls.evalParm('extcoeffb')],
                                                            look=hou.parmLook.ColorSquare, 
                                                            naming_scheme=hou.parmNamingScheme.RGBA)
                            out_parm.setMinValue(0)
                            out_parm.setMaxValue(2)
                            hasExtCoeff = True
                            parm.setExpression('ch(\"../../' + new_name + 'r\")')
                            folder.addParmTemplate(out_parm)
                            
                        else:
                            new_name = material.name + '_extcoeff' + parm.name().split('extcoeff')[1]
                            parm.setExpression('ch(\"../../' + new_name + '\")')
                    
                    elif 'fuzzcolor' in parm.name():
                        
                        if not hasFuzzCol:
                            
                            new_name = material.name + '_fuzzcolor'
                            print(new_name)
                            out_parm = hou.FloatParmTemplate(new_name, parm.description(), 3,
                                                            default_value=[controls.evalParm('fuzzcolorr'),controls.evalParm('fuzzcolorg'),controls.evalParm('fuzzcolorb')],
                                                            look=hou.parmLook.ColorSquare, 
                                                            naming_scheme=hou.parmNamingScheme.RGBA)
                            out_parm.setMinValue(0)
                            out_parm.setMaxValue(2)
                            hasFuzzCol = True
                            parm.setExpression('ch(\"../../' + new_name + 'r\")')
                            folder.addParmTemplate(out_parm)
                            
                        else:
                            new_name = material.name + '_fuzzcolor' + parm.name().split('fuzzcolor')[1]
                            parm.setExpression('ch(\"../../' + new_name + '\")')
                            
                    elif 'thin' in parm.name():
                        new_name = material.name + '_' + parm.name()
                        out_parm = hou.ToggleParmTemplate(new_name, parm.description())
                        parm.setExpression('ch(\"../../' + new_name + '\")')
                        folder.addParmTemplate(out_parm)
                    else:
                        new_name = material.name + '_' + parm.name()
                        out_parm = hou.FloatParmTemplate(new_name, parm.description(), 1, default_value=[parm.eval()])
                        out_parm.setMinValue(0)
                        out_parm.setMaxValue(1)
                        expression = 'ch(\"../../' + new_name + '\")'
                        parm.setExpression(expression)
                        folder.addParmTemplate(out_parm)


                    hou.node('.').setParmTemplateGroup(group)
            
        group.appendToFolder(('Materials'), folder)

    def update_UI(self):
        print('updating')
        hou.node('.').removeSpareParms()
        
        group = hou.node('.').parmTemplateGroup()

        for material in self.materials:
            self.create_parm_group(material, group)
        
        hou.node('.').setParmTemplateGroup(group, True)

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



