# Note: This code is just copied and pasted into the node right now... Looking for ways to link it :)
# https://www.sidefx.com/forum/topic/91717/?page=1#post-399671
from pipe.shared.helper.utilities.houdini_utils import HoudiniNodeUtils
myself = kwargs["node"]

file_cache_node = myself.createOutputNode("filecache::2.0")
file_cache_node.parm("filetype").set(1)

desired_name = "cache_vdb"
unique_name = HoudiniNodeUtils.get_unique_node_name(desired_name)
file_cache_node.setName(unique_name)

myself.setSelected(True)
file_cache_node.setSelected(True)

nodes_to_layout = [myself, file_cache_node]

myself.parent().layoutChildren(items = nodes_to_layout, horizontal_spacing=0.0, vertical_spacing=0.0)