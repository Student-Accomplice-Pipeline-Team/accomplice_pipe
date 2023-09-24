import hou
import os
import pipe


def on_created_callback(node):
    current_file = hou.hipFile.basename().split(".")[0]
    asset_names = node.parm("asset").menuItems()
    
    if current_file in asset_names:
        node.parm("asset").set(current_file)
        node.parm("asset_enabled").set(0)
    else:
        node.parm("asset").set("None")
        node.parm("asset_enabled").set(1)


def __verify_outnode(parent_node, node_dict):
    outnode = parent_node.node(node_dict[0])
    if not outnode:
        outnode = parent_node.createNode(node_dict[1], node_dict[0])
    outnode.parm("outputidx").set(node_dict[2])
    outnode.setPosition(node_dict[3])

    
def fix_internal_sop_outputs(node):
    """
    Fixes the 2 output nodes, in case they are accidentally deleted or moved.
    """
    
    DEFAULT     = ('default','output',0, hou.Vector2(0.0, -0.2))
    PROXY       = ('proxy','output',1 , hou.Vector2(2.4, -0.2))

    geo_network = node.node("sopnet/geo")
    
    for out_dict in [DEFAULT, PROXY]:
        __verify_outnode(geo_network, out_dict)


def get_asset_menu():
    asset_names = pipe.server.get_asset_list()
    menu_items = []
    
    for name in asset_names:
        menu_items.append(name)
        menu_items.append(name)
    
    return sorted(menu_items)
    

def asset_updated(node):
    node.parm("variant").set("None")
    hou.pwd().parm("save_path").set("")

    
def get_variant_menu():
    asset_name = hou.pwd().evalParm("asset")
    asset = pipe.server.get_asset(asset_name)
    
    if os.path.isdir(asset.get_geo_path()):
        menu_items = []
        
        path, _, files = next(os.walk(asset.get_geo_path()))
        
        if files:
            for file in files:
                menu_items.append(path + file)
                menu_items.append(file.split(".")[0])
        
        return menu_items
    
        
def get_save_names():
    geo_names = pipe.server.get_asset_list()
    
    menu_items = []
    
    for name in geo_names:
        asset = pipe.server.get_asset(name)
        
        if os.path.isdir(asset.get_geo_path()):
            path, _, files = next(os.walk(asset.get_geo_path()))
            
            if files:
                for file in files:
                    menu_items.append(path + file)
                    menu_items.append(asset.name + "_" + file.split(".")[0])
    
    return menu_items


def get_save_path():
    save_path = hou.pwd().evalParm("variant")
    
    if save_path == "None":
        hou.pwd().parm("save_path").set("")
    else:
        hou.pwd().parm("save_path").set(save_path)

def save():
    if hou.pwd().evalParm("save_path"):
        variant_parm = hou.pwd().parm("variant")
        variant_index = variant_parm.menuItems().index(variant_parm.eval())
        variant_label = variant_parm.menuLabels()[variant_index]
        
        if os.path.isfile(hou.pwd().evalParm("save_path")):
            response = hou.ui.displayMessage(
                f"\"{variant_label}\" already exists in the pipe. Are you sure you want to overwrite it?",
                buttons=("Overwrite", "Cancel"),
                severity=hou.severityType.ImportantMessage,
                default_choice=1
            )
        else:
            response = hou.ui.displayMessage(
                f"Are you sure you want to save \"{variant_label}\" to the pipe?",
                buttons=("Save", "Cancel"),
                severity=hou.severityType.ImportantMessage,
                default_choice=1
            )
        
        if response == 0:
            hou.pwd().node("save_to_disk").parm("execute").pressButton()
            hou.hipFile.save()
    
    else:
        hou.ui.displayMessage(
            "No \"Save Path\" has been set.",
            severity=hou.severityType.Error
        )


def save_as():
    asset_name = hou.pwd().evalParm("asset")
    print('This is the asset name!', asset_name)

    if asset_name:
        response = hou.ui.displayMessage(
            "Are you sure you want to create a new variant in the pipe? This cannot be \n"
            "undone without the help of a pipeline technician.",
            buttons=("Create a new variant", "Cancel"),
            severity=hou.severityType.ImportantMessage,
            default_choice=1,
            title="Create a New Variant?"
        )
        
        if response == 0:
            (response, variant_name) = hou.ui.readInput(
                "Give the variant a name. The name should be:\n"
                "    - one word\n"
                "    - all lowercase\n"
                "    - descriptive\n"
                "    - with no spaces or symbols\n"
                "\n"
                "For example, a variant of a table asset that adds an umbrella to the \n"
                "table could simply be named \"umbrella\".",
                buttons=("Create", "Cancel"),
                default_choice=1,
                close_choice=1,
                title="Name the Variant"
            )
            
            if response == 0:
                if not variant_name.isalpha() or not variant_name.islower():
                    hou.ui.displayMessage(
                        "An invalid variant name was entered",
                        severity=hou.severityType.Error
                    )
                    return
                
                # asset = pipe.server.get_asset(asset_name)
                variant = pipe.server.create_asset(variant_name, asset_name)
                save_path = variant.get_geo_path() + variant_name + ".usdc"
                
                if not os.path.exists(variant.get_geo_path()):
                    os.mkdir(variant.get_geo_path())
                
                _, _, files = next(os.walk(variant.get_geo_path()))
                for file in files:
                    if variant_name == file.split(".")[0]:
                        hou.ui.displayMessage(
                            f"A variant named \"{variant_name}\" already exists for asset \"{variant.name}.\"",
                            severity=hou.severityType.Error
                        )
                        return
                
                response = hou.ui.displayMessage(
                    f"Are you sure you want to save \"{variant_name}\" to the pipe?",
                    buttons=("Save", "Cancel"),
                    severity=hou.severityType.ImportantMessage,
                    default_choice=1
                )
                if response == 0:
                    # Create an empty file
                    with open(save_path, "w") as fp:
                        pass
                    
                    # Set the parameters to point to the empty file
                    hou.pwd().parm("variant").set(save_path)
                    hou.pwd().parm("save_path").set(save_path)
                    
                    # Write the file
                    hou.pwd().node("save_to_disk").parm("execute").pressButton()
                    hou.hipFile.save()

    else:
        hou.ui.displayMessage(
            "No \"Asset\" has been set.",
            severity=hou.severityType.Error
        )