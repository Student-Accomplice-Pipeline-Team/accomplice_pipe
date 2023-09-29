import hou
import pipe
from pipe.shared.object import Shot
from pipe.shared.helper.utilities.houdini_utils import HoudiniUtils, HoudiniNodeUtils
from pipe.shared.helper.utilities.usd_utils import UsdUtils
import os

shot_name = '' # TODO: if the user specifies a shot name, then we can pull in all the stuff relevant to that
if shot_name == '': # Assume that we are in a shot file
    shot = HoudiniUtils.get_shot_for_file()
else:
    shot = Shot(shot_name)

subnetwork_name = 'subnet1'
subnet = hou.node('/stage/' + subnetwork_name)

def create_new_reference_node(parent: hou.Node, department: str) -> hou.Node:
    reference = HoudiniNodeUtils.create_node(parent, 'reference')
    reference.setName(department)
    reference.parm('primpath1').set('/$OS')
    return reference

def get_reference_node(parent: hou.Node, department: str) -> hou.Node:
    if not HoudiniNodeUtils.node_exists(subnet, department):
        reference = create_new_reference_node(subnet, department)
    else:
        reference = subnet.node(department)
    return reference
"""
Pseudocode:
for each department:
    If it's main or layout, skip it (layout has its own node)
    if the node doesn't exist, create it (add this later, assume that the nodes do exist for now)
    Set the node path
"""
def update_department_reference_node_paths():
    department_reference_nodes = []
    for department in shot.available_departments:
        if department == 'main' or department == 'layout':
            continue
        # Get the reference nodes
        reference = get_reference_node(subnet, department)

        usd_path = shot.get_shot_usd_path(department)
        if not os.path.exists(usd_path):
            UsdUtils.create_empty_usd_at_filepath(usd_path)
        
        reference.parm('filepath1').set(shot.get_shot_usd_path(department))
        department_reference_nodes.append(reference)

# merge_node = HoudiniNodeUtils.create_node(subnet, 'merge')
# for reference_node in department_reference_nodes:
#     merge_node.setNextInput(reference_node)