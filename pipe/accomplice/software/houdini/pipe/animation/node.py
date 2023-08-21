import hou
import os, functools
import glob
# from pipe import Asset # This is producing this error: ImportError: cannot import name 'Asset' from 'pipe' (/groups/accomplice/pipeline/pipe/accomplice/software/houdini/pipe/__init__.py)
from pipe.shared.object import Asset

ANIM_SUBDIRECTORY = 'anim'

# NOTE: to be more cross platform, the code could use os.path.sep instead of '/', which is Linux specific.
# TODO: Get rid of all the old code

def get_asset(name: str) -> Asset:
    return pipe.server.get_asset(name)

def get_character_options_list():
    display_list = []

    hip_dir = os.path.dirname(hou.hipFile.path()) # $HIP directory

    # Check if the current directory has an anim folder
    anim_dir = os.path.join(hip_dir, ANIM_SUBDIRECTORY)

    if not os.path.isdir(anim_dir): # Error check
        hou.ui.displayMessage("There doesn't seem to be an anim folder in the context of this file. Open shot file and try again.")
        return []

    path_to_check = os.path.join(anim_dir, '**', '*.abc')
    for file in glob.iglob(path_to_check, recursive=True): # For each file in the anim directory
        if not 'anim_backup' in file:
            # Get the file name, not the full path
            split_file = file.split('/')
            anim = '/'.join(split_file[split_file.index(ANIM_SUBDIRECTORY)+1:])
            display_list.append(anim)
            display_list.append(anim[:-len('.abc')])

    return display_list

""" END CHARACTER NAME PARAMETER MENU SCRIPT """

def get_anim_name(node):
    return node.parm('./anim_name').eval()

def get_asset_name(node):
    return node.parm('./asset_name').eval()

def get_anim_description(node):
    return node.parm('./anim_descr').eval()

def publish_usd(node):
    print(node.path())
    usd_rop = hou.node(node.path() + '/USD_ANIM_EXPORT')
    usd_rop.parm('execute').pressButton()
    usd_rop = node.node('USD_VBLUR_EXPORT')
    usd_rop.parm('execute').pressButton()

def test_button(node):
    print("This is the test button!!!", node.path())


# gets called when a new character/object name is selected
def animUpdate(node):
    anim_path = node.parm('./anim_filename').eval()
    print("anim path: ", anim_path)

    anim_name = (anim_path.split('/')[-1])[0:-len('.abc')]
    anim_description = anim_name[anim_name.find('_')+1:]
    has_descr = anim_description.find('_') != -1
    if has_descr:
        asset_name = anim_description[:anim_description.find('_')]
    else:
        asset_name = anim_description
    print("anim name ", anim_name)
    print("asset name: ", asset_name)

    node.parm('./anim_name').set(anim_name)
    node.parm('./asset_name').set(asset_name)
    node.parm('./anim_descr').set(anim_description)

    node.allowEditingOfContents()
    setAnimType(node)
    charMatUpdate(node)
    # hairPrune(node)

def get_path_to_materials(node):
    asset_name = get_asset_name(node)
    # need to search for the right dir
    asset_dir = AccomplicePipe.get_asset_dir(asset_name)
    if asset_dir is None:
        return None
    return os.path.join(asset_dir, "materials")


def charMatUpdate(node):
    mat_sublayer = node.node('materials')
    path_to_materials = get_path_to_materials(node)
    if path_to_materials is None:
        hou.ui.displayMessage("Could not find asset's material folder. Alembic naming may not match. Please manually pull in the material folder to reference in the materials node within.")
    else:
        material_file = os.path.join(path_to_materials, get_asset_name(node) + "_shader.usda")
        mat_sublayer.parm('filepath1').set(material_file)

    mat = node.node('assign_material')
    mat.parm('nummaterials').set(1)
    mat.parm('primpattern1').set('/anim/`chs("../asset_name")`/geo')
    mat.parm('matspecpath1').set('/anim/`chs("../asset_name")`/materials/`chs("../asset_name")`_shader')

def setAnimType(node):
    anim_type = node.parm('anim_type')
    asset_name = get_asset_name(node)
    fx_bool = node.parm('fx_bool')
    if (asset_name.lower() == 'letty') or (asset_name.lower() == 'ed'):
        anim_type.set('human')
    else:
        anim_type.set('object')

    if (asset_name.lower() == 'letty') or (asset_name.lower() == 'ed'):
        fx_bool.set(1)
    else:
        fx_bool.set(0)
        
    # print(anim_type.eval())
    # print(str(fx_bool.eval()))

def prune(node):
    #make prim path list
    primPathList = []
    if (node.parm('hidetemphair').eval() == 1):
        if (node.parm('anim_type').eval() == 'human'):
            primPathList.append('/anim/`chs("../asset_name")`/geo/temp_hair')
            
    if (node.parm('hidetempcloth').eval() == 1) and (node.parm('anim_type').eval() == 'human'):
        primPathList.append('/anim/`chs("../asset_name")`/geo/temp_clothing')
        
    if (node.parm('hidefxgeo').eval() == 1) and (node.parm('fx_bool').eval() == 1):
        primPathList.append('/anim/`chs("../asset_name")`/geo/fx')
    
    #set prim path in the prune node
    prune = node.node('display_settings_prune')
    prune.parm('num_rules').set(len(primPathList))
    for i in range(0, len(primPathList)):
        primPattern = 'primpattern' + str(i+1)
        prune.parm('primpattern' + str(i+1)).set(primPathList[i])
        
        
def hairPrune(node):
    pass
    """
    hairPrune = node.node('maggie_hair_prune')
    if node.parm('anim_name').eval() == 'maggie':
        hairPrune.bypass(0)
    else:
        hairPrune.bypass(1)
    """
        
   