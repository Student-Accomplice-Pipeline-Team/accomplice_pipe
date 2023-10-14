import os
import pipe
import re
import hou
import json
from pipe.shared.helper.utilities.optimization_utils import DataCache

data_cache = DataCache()

class ImportLayout:
    def __init__(self, node: hou.Node=None): # Weirdly enough, 'node' apparently does't exist yet in the kwargs dictionary in the PythonModule, so some instances of this class will be created without a node passed in
        self.node = node

    def on_created(self):
        # This is necessary to ensure that the node doesn't attempt to load 
        # the USD file before the import_from parameter has been set.
        self.node.parm("import_from").set("default")

    def get_shot_menu(self):
        shot_names = data_cache.retrieve_from_cache('shot_list', pipe.server.get_shot_list)
        menu_items = []
        
        for shot_name in shot_names:
            shot = data_cache.retrieve_from_cache(shot_name, pipe.server.get_shot, shot_name)
            if os.path.isfile(shot.get_layout_path()):
                menu_items.append(shot_name)
                menu_items.append(shot_name)
        
        print('Shot menu items: ', menu_items)
        return sorted(menu_items)


    def get_usd_path(self):
        assert self.node is not None, "Node is None"

        path = None
        
        if self.node.evalParm("import_from") == "default":
        
            current_shot_name = hou.hipFile.basename()[:5]
            if re.match(r"[A-Z]_[0-9][0-9][0-9A-Z]", current_shot_name):
            
                shot_names = data_cache.retrieve_from_cache('shot_list', pipe.server.get_shot_list)
                current_shot_index = 0
                for shot_name in shot_names:
                    if shot_name == current_shot_name:
                        break
                    current_shot_index += 1
                
                previous_shot_index = current_shot_index - 1
                
                if "layout" in hou.hipFile.basename():
                    for index in range(previous_shot_index, -1, -1):
                        previous_shot = data_cache.retrieve_from_cache(shot_names[index], pipe.server.get_shot, shot_names[index])
                        if os.path.isfile(previous_shot.get_layout_path()):
                            path = previous_shot.get_layout_path()
                            break
                else:
                    current_shot = data_cache.retrieve_from_cache(current_shot_name, pipe.server.get_shot, current_shot_name)
                    
                    if os.path.isfile(current_shot.get_layout_path()):
                        path = current_shot.get_layout_path()
                    else:
                        for index in range(previous_shot_index, -1, -1):
                            previous_shot = data_cache.retrieve_from_cache(shot_names[index], pipe.server.get_shot, shot_names[index])
                            if os.path.isfile(previous_shot.get_layout_path()):
                                path = previous_shot.get_layout_path()
                                break
            
        elif self.node.evalParm("import_from") == "specified_shot":
            shot_name = self.node.evalParm("specified_shot")
            shot = data_cache.retrieve_from_cache(shot_name, pipe.server.get_shot, shot_name)
            path = shot.get_layout_path()
            
        return path

