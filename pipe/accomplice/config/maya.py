import os

# System Dirs
script_path = os.environ.get("MAYA_SCRIPT_PATH")
xbmlangpath = os.environ.get("XBMLANGPATH")

# USD
usd_export_map1_as_primary_uv_set = os.environ.get("MAYAUSD_EXPORT_MAP1_AS_PRIMARY_UV_SET")
usd_import_primary_uv_set_as_map1 = os.environ.get("MAYAUSD_IMPORT_PRIMARY_UV_SET_AS_MAP1")

# Packages that should get reloaded by maya.packages.unload
packages_to_reload = ["pipe"]