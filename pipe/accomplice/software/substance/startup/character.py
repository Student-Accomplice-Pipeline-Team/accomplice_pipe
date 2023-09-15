from PySide2 import QtWidgets 
import substance_painter.ui 

# Substance 3D Painter modules
import substance_painter.ui
import substance_painter.project

plugin_widgets = [] 
"""Keep track of added ui elements for cleanup""" 
 
def start_plugin(): 
    # Create a text widget for a menu
	Action = QtWidgets.QAction("Accomplice - Reload Geometry")
	Action.triggered.connect(reload_mesh)

	# Add this widget to the existing File menu of the application
	substance_painter.ui.add_action(
		substance_painter.ui.ApplicationMenu.File,
		Action )

	# Store the widget for proper cleanup later when stopping the plugin
	plugin_widgets.append(Action)
 
def close_plugin(): 
    """This method is called when the plugin is stopped.""" 
    # We need to remove all added widgets from the UI. 
    for widget in plugin_widgets: 
        substance_painter.ui.delete_ui_element(widget) 
    plugin_widgets.clear()

def reload_mesh():
    if not substance_painter.project.is_open():
        QtWidgets.QMessageBox.warning(None, "No project open", "Please open a project before trying to reload a mesh.")
        return

    mesh_path = substance_painter.project.last_imported_mesh_path()

    settings = substance_painter.project.MeshReloadingSettings(import_cameras = False, preserve_strokes=True)

    substance_painter.project.reload_mesh(mesh_path, settings, completed)

def completed(loaded_status):
    print('RELOAAAADDDED!')
    print(loaded_status)
 
if __name__ == "__main__": 
    start_plugin() 