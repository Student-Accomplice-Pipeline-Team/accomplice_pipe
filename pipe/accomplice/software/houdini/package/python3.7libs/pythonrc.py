"""Initialize the Houdini pipeline environment on startup."""
import pipe
import logging
import os
from pathlib import *
import hou

"""Import HDAs"""

# As far as I can tell, this code isn't being called and it's already handled by setting the environment variables anyway
# """Yeah... I know it uses absolute file path right now, I'll fix it later"""
# hda_directory = Path("/groups/accomplice/pipeline/pipe/accomplice/software/houdini_new/pipe/hda")

# for path in hda_directory.glob("*.hdanc"):
#     hou.hda.installFile(str(Path(path).resolve()))

