import hou
import os
import pxr
import random
import pipe
from pipe.shared.object import *
from pathlib import *
import pipe.shared.versions as vs
import pipe.tools.shading.edit_shader as edit

MATLIB_NAME = "Material_Library"


class Character_Shaders(edit.EditShader):
    def __init__(self):
        print("starting...")
        self.character = None
        self.asset = None
        self.materials = {}
        self.materialVariant = None
        self.geo_variant_name = None
        self.texturesPath = None
        self.nodes_path = None

    def get_character_menu(self):
        character_names = pipe.server.get_character_list()
        menu_items = []

        for name in character_names:
            menu_items.append(name)
            menu_items.append(name)

        return sorted(menu_items)

    def set_character(self, character, node):
        if character != "None":
            self.character = pipe.server.get_character(character)
            self.asset = self.character
            node.parm("toggle").set(1)
            print(self.character.path)

            ref = node.node("reference1")
            ref.parm("primpath").set("/" + self.character.name + "/materials")

        else:
            node.parm("toggle").set(0)
        print(character)

    def switch(self, node):
        parm = node.parm("input")

        if self.character:
            if self.character.name == "letty":
                parm.set(0)
            elif self.character.name == "ed":
                parm.set(1)
            elif self.character.name == "vaughn":
                parm.set(2)
            elif self.character.name == "studentcar":
                parm.set(3)
            elif self.character.name == "bgcharacter":
                parm.set(4)

    def export_USD(self, node):
        save_node = node.node("saveUSD")
        save_path = self.character.get_material_path()

        print(save_path)
        version_path = vs.get_next_version(save_path)

        save_node.parm("lopoutput").set(version_path)
        save_node.parm("execute").pressButton()

        vs.update_symlink(save_path, version_path)

    def load_USD(self, node):
        stage = node.parent()

        sublayer = stage.createNode(
            "reference", node_name=self.character.name + "_materials"
        )
        sublayer.parm("filepath1").set(self.character.get_material_path())
        node.setInput(1, sublayer)

    def create_materials(self):
        metadata = self.asset.get_metadata()
        self.geo_variant_name = "Standard"
        self.materialVariant = metadata.hierarchy[self.geo_variant_name][
            self.character.name
        ]
        self.texturesPath = self.asset.get_textures_path()

        for _, material in self.materialVariant.materials.items():
            self.materials[material] = {}

        super().create_materials()

    def matLib(self):
        return hou.node("./" + MATLIB_NAME)
