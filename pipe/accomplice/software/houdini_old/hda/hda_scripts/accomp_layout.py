import hou


def type(node):
    node.allowEditingOfContents()
    print(node.parm("layouttype").eval())
    sublayer = node.node("layout")
    sublayer.parm("filepath1").set(node.parm("layouttype").eval())
    sublayer.parm("reload").pressButton()


def unlock(node):
    node.allowEditingOfContents()


def reload(node):
    sublayer = node.node("layout")
    sublayer.parm("reload").pressButton()


def areaPrune(node):
    node.allowEditingOfContents()
    primitivepaths = ""
    if node.parm("hide_ceilings").eval() == 1:
        primitivepaths += "/layout/ceiling_area "
    if node.parm("hide_frontdoor").eval() == 1:
        primitivepaths += "/layout/front_door_area/fallen_leaves /layout/front_door_area/flowerpot_giant_front /layout/front_door_area/FLOOR_FLOWERS "
    if node.parm("hide_sewing").eval() == 1:
        primitivepaths += "/layout/sewing_area/SHELF_BOT /layout/sewing_area/SHELF_TOP /layout/sewing_area/TABLE /layout/sewing_area/WALL_ASSETS "
    if node.parm("hide_sidedoor").eval() == 1:
        primitivepaths += "/layout/side_door_area/CHAIR /layout/side_door_area/bottle_pantry_d /layout/side_door_area/bottle_pantry_e /layout/side_door_area/bottle_pantry_f /layout/side_door_area/bucket /layout/side_door_area/mat_side_door /layout/side_door_area/trunk_guillo "
    if node.parm("hide_couch").eval() == 1:
        primitivepaths += "/layout/couch_area/NOOK_SHELVES /layout/couch_area/TABLE_COUCH /layout/couch_area/WALL_ASSETS /layout/couch_area/barrel /layout/couch_area/basket_couch /layout/couch_area/couch /layout/couch_area/drapery_couch_wall /layout/couch_area/grain_bag_couch /layout/couch_area/iron_maiden /layout/couch_area/rake /layout/couch_area/rug_couch_large /layout/couch_area/staff "
    if node.parm("hide_fireplace").eval() == 1:
        primitivepaths += "/layout/fireplace_area/FIREPLACE/firewood /layout/fireplace_area/FIREPLACE/picture_hanging_a /layout/fireplace_area/FIREPLACE/picture_hanging_b /layout/fireplace_area/FIREPLACE/picture_hanging_c /layout/fireplace_area/FIREPLACE/picture_hanging_d /layout/fireplace_area/FIREPLACE/picture_hanging_e /layout/fireplace_area/FIREPLACE/picture_hanging_f /layout/fireplace_area/FIREPLACE/spellbook_holder /layout/fireplace_area/FIREPLACE/spellbook_main /layout/fireplace_area/FIREPLACE/spellbook_secondary /layout/fireplace_area/FIREPLACE/stones_floor_fireplace /layout/fireplace_area/FIREPLACE/vase_fireplace /layout/fireplace_area/LEFT_SHELVES /layout/fireplace_area/POTS_PANS /layout/fireplace_area/RIGHT_SHELF /layout/fireplace_area/TABLE /layout/fireplace_area/carpet_standing /layout/fireplace_area/chair_fireplace /layout/fireplace_area/coal_fireplace /layout/fireplace_area/knitting_basket /layout/fireplace_area/tools_fireplace /layout/fireplace_area/wood_fireplace "
    if node.parm("hide_kitchen").eval() == 1:
        primitivepaths += "/layout/kitchen_area/PANTRY/SHELF_A /layout/kitchen_area/PANTRY/SHELF_B /layout/kitchen_area/PANTRY/SHELF_C /layout/kitchen_area/PANTRY/SHELF_D /layout/kitchen_area/PANTRY/SHELF_E /layout/kitchen_area/PANTRY/bellows /layout/kitchen_area/PANTRY/bucket /layout/kitchen_area/PANTRY/dried_flowers_hanging /layout/kitchen_area/PANTRY/ham_hanging /layout/kitchen_area/PANTRY/mushroom_basket /layout/kitchen_area/PANTRY/pan_pantry /layout/kitchen_area/PANTRY/pot_pantry /layout/kitchen_area/PANTRY/scale /layout/kitchen_area/SHELF /layout/kitchen_area/STOVE /layout/kitchen_area/TABLE "
    if node.parm("hide_dining").eval() == 1:
        primitivepaths += "/layout/dining_area/ARMOIRE /layout/dining_area/TABLE /layout/dining_area/chair_dining_prince /layout/dining_area/chair_dining_witch /layout/dining_area/chandelier /layout/dining_area/rug_dining_large /layout/dining_area/rug_dining_secondary "
    node.node("objects_prune").parm("primpattern1").set(primitivepaths)
