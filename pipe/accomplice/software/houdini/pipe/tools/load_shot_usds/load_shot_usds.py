import hou
from pipe.shared.object import Shot
from pipe.shared.helper.utilities.houdini_utils import HoudiniUtils, HoudiniNodeUtils
from pipe.shared.helper.utilities.usd_utils import UsdUtils
from pipe.shared.helper.utilities.optimization_utils import DataCache
import os

data_cache = DataCache()

class LoadShotUsds: # TODO: note that this node has been updated to be called 'accomp_load_department_layers' in the hda. When you have time, it would make sense to rewrite this code so that people don't get confused.
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
                UsdUtils.create_usd_with_department_prim(usd_path, department)
            
            # reference.parm('filepath1').set(shot.get_shot_usd_path(department))
            # department_reference_nodes.append(reference)
            myself.parm(department + '_usd_path').set(usd_path)

    def set_current_department(myself: hou.Node, department=None):
        if department is None:
            department = HoudiniUtils.get_department()
        print('my department is:', department)
        myself.parm('current_department').set(department)

    def uncheck_current_department(myself: hou.Node):
        """ Callback for when the current department dropdown is changed """
        # Set the corresponding checkbox for that department to false
        current_department = myself.parm('current_department').eval()
        if current_department != 'main':
            checkbox = myself.parm('include_' + current_department)
            checkbox.set(0)

    def on_created(myself: hou.Node):
        # shot = HoudiniUtils.get_shot_for_file()
        shot = data_cache.retrieve_from_cache('shot', HoudiniUtils.get_shot_for_file)
        # import pdb; pdb.set_trace()
        # print('THIS IS THE SHOT NAME! :', shot)
        user_selected_department = None
        if shot is None:
            hou.ui.displayMessage("It appears that you are not using a shot file. To simulate being in a shot file, you can select a shot with the following menu.")
            shot, user_selected_department = HoudiniUtils.prompt_user_for_shot_and_department()
        
        LoadShotUsds.update_department_reference_node_paths(myself, shot)
        if user_selected_department is not None:
            LoadShotUsds.set_current_department(myself, user_selected_department)
        else:
            LoadShotUsds.set_current_department(myself)
        LoadShotUsds.uncheck_current_department(myself)

    
    def get_shot_usd_path(department_specific=False):
        shot = data_cache.retrieve_from_cache('shot', HoudiniUtils.get_shot_for_file)
        if department_specific:
            return shot.get_shot_usd_path(HoudiniUtils.get_department())
        else:
            return shot.get_shot_usd_path()
    
    def refresh_all_reference_nodes(myself: hou.Node):
        for department in Shot.available_departments:
            if department == 'main':
                continue
            myself.parm('reload_' + department).pressButton()