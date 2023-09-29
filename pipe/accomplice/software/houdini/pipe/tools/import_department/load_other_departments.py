import hou
import pipe
from pipe.shared.object import Shot
from pipe.shared.helper.utilities.houdini_utils import HoudiniUtils

shot = HoudiniUtils.get_shot_for_file()

subnetwork_name = 'subnet1'
subnet = hou.node('/stage/' + subnetwork_name)
from pipe.shared.helper.utilities.houdini_utils import HoudiniNodeUtils

def create_new_reference_node(parent: hou.Node, department: str) -> hou.Node:
    reference = HoudiniNodeUtils.create_node(parent, 'reference')
    reference.setName(department)
    reference.parm('primpath1').set('/$OS')
    return reference

department_reference_nodes = []
for department in shot.available_departments:
    reference.parm('filepath1').set(shot.get_shot_usd_path(department))
    department_reference_nodes.append(reference)

merge_node = HoudiniNodeUtils.create_node(subnet, 'merge')
for reference_node in department_reference_nodes:
    merge_node.setNextInput(reference_node)