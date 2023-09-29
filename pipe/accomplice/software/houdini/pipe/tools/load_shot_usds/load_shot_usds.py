import hou
from pipe.shared.object import Shot
from pipe.shared.helper.utilities.houdini_utils import HoudiniUtils, HoudiniNodeUtils
from pipe.shared.helper.utilities.usd_utils import UsdUtils
import os

class LoadShotUsds:
    def get_departments_menu_list():
        # Houdini dropdown menues must have an even number of items
        menu_options = []
        for department in Shot.available_departments:
            menu_options.append(department)
            menu_options.append(department)
        return menu_options

    def create_new_reference_node(parent: hou.Node, department: str) -> hou.Node:
        reference = HoudiniNodeUtils.create_node(parent, 'reference')
        reference.setName(department)
        reference.parm('primpath1').set('/$OS')
        return reference

    def get_reference_node(parent: hou.Node, department: str) -> hou.Node:
        # if not HoudiniNodeUtils.node_exists(myself, department):
        #     reference = LoadShotUsds.create_new_reference_node(myself, department) # TODO: This will need to be connected to the merge node :)
        assert HoudiniNodeUtils.node_exists(parent, department), f"Reference node for department {department} does not exist."
        reference = parent.node(department)
        return reference

    def update_department_reference_node_paths(myself:hou.Node, shot: Shot):
        # department_reference_nodes = []
        for department in shot.available_departments:
            if department == 'main' or department == 'layout':
                continue
            # Get the reference nodes
            # reference = LoadShotUsds.get_reference_node(myself, department)

            usd_path = shot.get_shot_usd_path(department)
            if not os.path.exists(usd_path):
                UsdUtils.create_empty_usd_at_filepath(usd_path, department)
            
            # reference.parm('filepath1').set(shot.get_shot_usd_path(department))
            # department_reference_nodes.append(reference)
            myself.parm(department + '_usd_path').set(usd_path)

    def set_current_department(myself: hou.Node, department: str):
        myself.parm('current_department').set(department)

    def on_created(myself: hou.Node):
        shot = HoudiniUtils.get_shot_for_file()
        if shot is None:
            # Inform user that they're not in a shot file
            hou.ui.displayMessage("It appears that you are not using a shot file. Please open a file that's in the subdirectory of a shot.")
            # TODO: Give the user the opportunity to open a shot file
            return
        
        LoadShotUsds.update_department_reference_node_paths(myself, shot)
        LoadShotUsds.set_current_department(myself, HoudiniUtils.get_department())