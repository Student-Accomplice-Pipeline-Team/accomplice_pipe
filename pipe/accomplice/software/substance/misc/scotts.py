from PySide2 import QtWidgets, QtGui
from typing import Optional

import os
import substance_painter as sp

global ostrich_tools


def start_plugin() -> None:
    """This method is called when the plugin is started."""
    global ostrich_tools
    ostrich_tools = OstrichTools()
    print("Started Ostrich Tools")


def close_plugin() -> None:
    """This method is called when the plugin is stopped."""
    global ostrich_tools
    del ostrich_tools


class OstrichTools:
    def __init__(self):
        self.plugin_widgets = []

        self.DEFAULT_ENVMAP = "hall_of_mammals_4k.hdr"
        self.DEFAULT_OUTPUT_TEMPLATE = "ue4_ostrich.spexp"
        self.DEFAULT_TEMPLATE_NAME = "Unreal Engine 4 (OSTRICH)"

        self.output_template: sp.resource.Resource

        self.buildUI()
        sp.event.DISPATCHER.connect(sp.event.ProjectCreated, self.on_project_open)
        sp.event.DISPATCHER.connect(sp.event.ProjectOpened, self.on_project_open)

    def __del__(self):
        for widget in self.plugin_widgets:
            sp.ui.delete_ui_element(widget)

    def buildUI(self) -> None:
        """Build the UI"""

        opal = QtGui.QIcon(self.get_resource("opal.png"))
        toolbar_button = QtWidgets.QToolButton()
        toolbar_button.setToolTip("Ostrich Tools")
        toolbar_button.setIcon(opal)
        toolbar_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        menu = QtWidgets.QMenu("Ostrich Tools", toolbar_button)
        toolbar_button.setMenu(menu)

        mask_action = QtWidgets.QAction("Add mask layers to current texture set", menu)
        mask_action.triggered.connect(self.set_up_masks)
        menu.addAction(mask_action)

        opacity_action = QtWidgets.QAction(
            "Add opacity layer to current texture set", menu
        )
        opacity_action.triggered.connect(self.set_up_opacity)
        menu.addAction(opacity_action)

        export_action = QtWidgets.QAction("Export", menu)
        export_action.triggered.connect(self.do_export)
        menu.addAction(export_action)

        sp.ui.add_plugins_toolbar_widget(toolbar_button)

        self.plugin_widgets.append(toolbar_button)

    def on_project_open(self, event: sp.event.Event) -> None:
        """Keep imported resources up to date on project open"""

        # update/import the envmap
        envmap_old_url = sp.project.Metadata("OstrichTools").get("default_envmap")
        envmap_new = self.import_envmap(self.DEFAULT_ENVMAP)
        if envmap_old_url:
            envmap_old = sp.resource.ResourceID.from_url(envmap_old_url)
            sp.resource.update_layer_stack_resource(envmap_old, envmap_new)
        else:
            sp.project.Metadata("OstrichTools").set(
                "default_envmap", envmap_new.identifier().url()
            )
            print(f"Setting envmap: { self.DEFAULT_ENVMAP }")
            sp.display.set_environment_resource(envmap_new.identifier())

        # import the output template
        self.output_template = self.import_output_template(
            self.DEFAULT_OUTPUT_TEMPLATE, self.DEFAULT_TEMPLATE_NAME
        )

    def import_output_template(
        self, filename: str, template_name: Optional[str]
    ) -> sp.resource.Resource:
        """Import an Output Template to the session"""
        print(f"Importing output template: { filename }")

        file_path = self.get_resource(filename)
        template = sp.resource.import_session_resource(
            file_path, sp.resource.Usage.EXPORT, template_name
        )

        return template

    def import_envmap(self, filename: str) -> sp.resource.Resource:
        """Import an environment map to the project"""
        envmap_path = self.get_resource(filename)
        return sp.resource.import_project_resource(
            envmap_path, sp.resource.Usage.ENVIRONMENT
        )

    def get_texture_dir(self) -> str:
        """Get the default asset save path, creating if not exists"""

        current_asset = sp.project.last_imported_mesh_path()
        asset_dir = os.path.dirname(current_asset)
        texture_dir = os.path.join(asset_dir, "textures")
        if not os.path.exists(texture_dir):
            os.mkdir(texture_dir)
        return texture_dir

    def set_up_masks(self) -> None:
        if not sp.project.is_open():
            QtWidgets.QMessageBox.warning(
                None, "No project open", "Please open a project before setting up masks"
            )
            return

        # get currently active layer stack (paintable)
        stack = sp.textureset.get_active_stack()

        if not stack.has_channel(sp.textureset.ChannelType.User0):
            stack.add_channel(
                sp.textureset.ChannelType.User0,
                sp.textureset.ChannelFormat.L8,
                "Mask 1",
            )
        if not stack.has_channel(sp.textureset.ChannelType.User1):
            stack.add_channel(
                sp.textureset.ChannelType.User1,
                sp.textureset.ChannelFormat.L8,
                "Mask 2",
            )

    def set_up_opacity(self) -> None:
        if not sp.project.is_open():
            QtWidgets.QMessageBox.warning(
                None,
                "No project open",
                "Please open a project before setting up opacity",
            )
            return

        # get currently active layer stack (paintable)
        stack = sp.textureset.get_active_stack()

        if not stack.has_channel(sp.textureset.ChannelType.Opacity):
            stack.add_channel(
                sp.textureset.ChannelType.Opacity, sp.textureset.ChannelFormat.L8
            )

    def do_export(self) -> None:
        """Export the textures"""
        # with much thanks to Gabe Reed

        if not sp.project.is_open():
            QtWidgets.QMessageBox.warning(
                None,
                "No project open",
                "Please open a project before exporting textures",
            )
            return

        export_path = self.get_texture_dir()
        if not export_path.endswith("/"):
            export_path += "/"

        output_template_url = self.output_template.identifier().url()

        export_config = {
            "exportShaderParams": False,
            "exportPath": export_path,
            "exportPresets": [
                {
                    "name": "default",
                    "maps": [],
                }
            ],
            "defaultExportPreset": output_template_url,
            "exportParameters": [
                {
                    "parameters": {
                        "paddingAlgorithm": "infinite",
                    },
                }
            ],
        }

        error = False
        for ts in sp.textureset.all_texture_sets():
            print(f"Exporting texture set: { ts.name() } !")

            stack = ts.get_stack()
            try:
                sp.export.export_project_textures(
                    {
                        **export_config,
                        "exportList": [
                            {
                                "rootPath": str(stack),
                            }
                        ],
                    }
                )
                print(f"Exported textures to { export_path }")
            except Exception as e:
                error = True
                print(e)
                QtWidgets.QMessageBox.warning(
                    None,
                    "Error",
                    "An error occurred while exporting the textures. Please check the console for more information.",
                )

        if not error:
            QtWidgets.QMessageBox.information(
                None, "Export complete", "Textures exported successfully."
            )

    def get_resource(self, filename: str) -> str:
        """Get absolute path to resource in resource directory"""
        resource_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, "resources")
        )
        return os.path.join(resource_dir, filename)


if __name__ == "__main__":
    print("Please work from here")
    start_plugin()
