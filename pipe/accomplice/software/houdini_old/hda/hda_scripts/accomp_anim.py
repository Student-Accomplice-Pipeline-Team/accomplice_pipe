import hou
import os, functools
import glob
from accomplice import AccomplicePipe

""" BEGIN CHARACTER NAME PARAMETER MENU SCRIPT """


def get_character_options_list():
    display_list = []

    hip_dir = os.path.dirname(hou.hipFile.path())  # hip directory
    # Check if user is at least in the shots directories
    # check if the current directory has an anim folder
    anim_dir = os.path.join(hip_dir, "anim")
    if os.path.isdir(anim_dir):
        path_to_check = os.path.join(anim_dir, "**", "*.abc")
        for file in glob.iglob(path_to_check, recursive=True):
            # don't take if it has anim_backup in the path
            if not "anim_backup" in file:
                # get the file name, not the full path
                split_file = file.split("/")
                anim = "/".join(split_file[split_file.index("anim") + 1 :])
                display_list.append(anim)
                display_list.append(anim[: -len(".abc")])
    else:
        hou.ui.displayMessage(
            "There doesn't seem to be an anim folder in the context of this file. Go to a shot file and try again."
        )

    return display_list


""" END CHARACTER NAME PARAMETER MENU SCRIPT """


def get_anim_name(node):
    return node.parm("./anim_name").eval()


def get_asset_name(node):
    return node.parm("./asset_name").eval()


def get_anim_description(node):
    return node.parm("./anim_descr").eval()


def publishUsd(node):
    print(node.path())
    usd_rop = hou.node(node.path() + "/USD_ANIM_EXPORT")
    usd_rop.parm("execute").pressButton()
    usd_rop = node.node("USD_VBLUR_EXPORT")
    usd_rop.parm("execute").pressButton()


# gets called when a new character/object name is selected
def animUpdate(node):
    anim_path = node.parm("./anim_filename").eval()
    print("anim path: ", anim_path)

    anim_name = (anim_path.split("/")[-1])[0 : -len(".abc")]
    anim_description = anim_name[anim_name.find("_") + 1 :]
    has_descr = anim_description.find("_") != -1
    if has_descr:
        asset_name = anim_description[: anim_description.find("_")]
    else:
        asset_name = anim_description
    print("anim name ", anim_name)
    print("asset name: ", asset_name)

    node.parm("./anim_name").set(anim_name)
    node.parm("./asset_name").set(asset_name)
    node.parm("./anim_descr").set(anim_description)

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
    return os.path.join(asset_dir, "material")


def charMatUpdate(node):
    mat_sublayer = node.node("materials")
    path_to_materials = get_path_to_materials(node)
    if path_to_materials is None:
        hou.ui.displayMessage(
            "Could not find asset's material folder. Alembic naming may not match. Please manually pull in the material folder to reference in the materials node within."
        )
    else:
        material_file = os.path.join(
            path_to_materials, get_asset_name(node) + "_shader.usda"
        )
        mat_sublayer.parm("filepath1").set(material_file)

    mat = node.node("assign_material")
    mat.parm("nummaterials").set(1)
    mat.parm("primpattern1").set('/anim/`chs("../asset_name")`/geo')
    mat.parm("matspecpath1").set(
        '/anim/`chs("../asset_name")`/materials/`chs("../asset_name")`_shader'
    )


def setAnimType(node):
    anim_type = node.parm("anim_type")
    asset_name = get_asset_name(node)
    fx_bool = node.parm("fx_bool")
    if (asset_name.lower() == "letty") or (asset_name.lower() == "ed"):
        anim_type.set("human")
    else:
        anim_type.set("object")

    if (asset_name.lower() == "letty") or (asset_name.lower() == "ed"):
        fx_bool.set(1)
    else:
        fx_bool.set(0)

    # print(anim_type.eval())
    # print(str(fx_bool.eval()))


def do_material(node):
    if node.parm("do_material").eval() == 0:
        hou.node("./switch_shading").parm("input").set(0)
    else:
        hou.node("./switch_shading").parm("input").set(1)


def publish_assign_mat_rules(node):
    asset_name = get_asset_name(node)
    # need to search for the right dir
    asset_dir = AccomplicePipe.get_asset_dir(asset_name)

    # if there is an exisitng camera, see if the user really wants to override it
    filepath = os.path.join(asset_dir, "assign_mat_rule.txt")
    if os.path.is_file(filepath):
        message = "Do you want to override the assign mat rule on disk?"
        button0 = "yes"
        button1 = "no"
        title = "Assign Mat Rule"

        userInput = hou.ui.displayMessage(
            message, buttons=(button0, button1), title=title
        )
        # Stop process if the user does not want to reimport
        if userInput == 1:
            return

    f = open(filepath, "w")

    assign_mat_node = hou.node("assign_material")
    nummat = assign_mat_node.parm("nummaterials")

    for i in range(1, nummat + 1):
        primpattern = assign_mat_node.parm("primpattern" + str(i))
        matspecpath = assign_mat_node.parm("matspecpath" + str(i))


def prune(node):
    # make prim path list
    primPathList = []
    if node.parm("hidetemphair").eval() == 1:
        if node.parm("anim_type").eval() == "human":
            primPathList.append('/anim/`chs("../asset_name")`/geo/temp_hair')

    if (node.parm("hidetempcloth").eval() == 1) and (
        node.parm("anim_type").eval() == "human"
    ):
        primPathList.append('/anim/`chs("../asset_name")`/geo/temp_clothing')

    if (node.parm("hidefxgeo").eval() == 1) and (node.parm("fx_bool").eval() == 1):
        primPathList.append('/anim/`chs("../asset_name")`/geo/fx')

    # set prim path in the prune node
    prune = node.node("display_settings_prune")
    prune.parm("num_rules").set(len(primPathList))
    for i in range(0, len(primPathList)):
        primPattern = "primpattern" + str(i + 1)
        prune.parm("primpattern" + str(i + 1)).set(primPathList[i])


def hairPrune(node):
    pass
    """
    hairPrune = node.node('maggie_hair_prune')
    if node.parm('anim_name').eval() == 'maggie':
        hairPrune.bypass(0)
    else:
        hairPrune.bypass(1)
    """
