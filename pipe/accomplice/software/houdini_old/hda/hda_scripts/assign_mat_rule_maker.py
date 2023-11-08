import os

node = hou.pwd()
stage = node.editableStage()

hip = hou.hipFile.path()
# filepath =
num_assigns = hou.evalParm("../assign_material/nummaterials")

primpatterns = []
matspecpaths = []

rules = {}
for i in range(num_assigns):
    prim_pattern_parm = "../assign_material/primpattern" + str(i + 1)
    primpatterns.append(hou.evalParm(prim_pattern_parm))

    mat_pattern_parm = "../assign_material/matspecpath" + str(i + 1)
    matspecpaths.append(hou.evalParm(mat_pattern_parm))

    rules[matspecpaths[i]] = primpatterns[i]

hou.ui.displayMessage(str(rules))
