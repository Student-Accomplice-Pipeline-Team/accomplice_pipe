import os
import pipe
import re
import hou
import json

class CachedDataManager:
    def __init__(self):
        self.cache = {}
    def retrieve_from_cache(self, key, loader_function=None, function_input=None):
        if key in self.cache:
            print('Retrieving from cache: ', key)
            return self.cache[key]
        else:
            print('Caching key: ', key)
            assert loader_function is not None, f"Key {key} not found in cache and no loader function was provided."
            if function_input is None:
                value = loader_function()
            else:
                value = loader_function(function_input)
            self.cache[key] = value
            self.cache[key + '_function'] = loader_function
            self.cache[key + '_function_input'] = function_input
            return value

    def reload_cached_items(self):
        for key in self.cache:
            if key.endswith('function'):
                self.cache[key.replace('function', '')] = self.cache[key](self.cache[key + '_function_input'])

cache_data_manager = CachedDataManager()

class ImportLayout:
    def __init__(self, node: hou.Node=None):
        self.node = node

    def on_created(self):
        # This is necessary to ensure that the node doesn't attempt to load 
        # the USD file before the import_from parameter has been set.
        self.node.parm("import_from").set("default")

    def get_shot_menu(self):
        shot_names = cache_data_manager.retrieve_from_cache('shot_list', pipe.server.get_shot_list)
        menu_items = []
        
        for shot_name in shot_names:
            shot = cache_data_manager.retrieve_from_cache(shot_name, pipe.server.get_shot, shot_name)
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
            
                shot_names = cache_data_manager.retrieve_from_cache('shot_list', pipe.server.get_shot_list)
                current_shot_index = 0
                for shot_name in shot_names:
                    if shot_name == current_shot_name:
                        break
                    current_shot_index += 1
                
                previous_shot_index = current_shot_index - 1
                
                if "layout" in hou.hipFile.basename():
                    for index in range(previous_shot_index, -1, -1):
                        previous_shot = cache_data_manager.retrieve_from_cache(shot_names[index], pipe.server.get_shot, shot_names[index])
                        if os.path.isfile(previous_shot.get_layout_path()):
                            path = previous_shot.get_layout_path()
                            break
                else:
                    current_shot = cache_data_manager.retrieve_from_cache(current_shot_name, pipe.server.get_shot, current_shot_name)
                    
                    if os.path.isfile(current_shot.get_layout_path()):
                        path = current_shot.get_layout_path()
                    else:
                        for index in range(previous_shot_index, -1, -1):
                            previous_shot = cache_data_manager.retrieve_from_cache(shot_names[index], pipe.server.get_shot, shot_names[index])
                            if os.path.isfile(previous_shot.get_layout_path()):
                                path = previous_shot.get_layout_path()
                                break
            
        elif self.node.evalParm("import_from") == "specified_shot":
            shot_name = self.node.evalParm("specified_shot")
            shot = pipe.server.get_shot(shot_name) # CACHE THIS
            path = shot.get_layout_path()
            
        return path

