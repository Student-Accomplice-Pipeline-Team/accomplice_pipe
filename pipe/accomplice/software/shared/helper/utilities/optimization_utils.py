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
    
    def reload_cached_item(self, key):
        assert key in self.cache, f"Key {key} not found in cache."
        function_key = key + '_function'
        function_input_key = key + '_function_input'
        if function_input_key is not None:
            self.cache[key] = self.cache[function_key](self.cache[function_input_key])
        else:
            self.cache[key] = self.cache[function_key]()
        return self.cache[key]