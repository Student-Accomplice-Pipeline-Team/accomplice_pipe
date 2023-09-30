class DataCache:
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