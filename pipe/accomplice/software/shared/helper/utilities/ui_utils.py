from PySide2 import QtWidgets

class ListWithFilter(QtWidgets.QDialog):
    def __init__(self, title:str, items:list, parent=None):
        super(ListWithFilter, self).__init__(parent)
        self.setWindowTitle(title)
        
        self.resize(500, 600)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # Filter field
        self.filter_field = QtWidgets.QLineEdit()
        layout.addWidget(self.filter_field)

        # List box
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(items)
        layout.addWidget(self.list_widget)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        # Connect signals
        self.filter_field.textChanged.connect(self.filter_items)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def filter_items(self):
        filter_text = self.filter_field.text().lower()
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            item_text = item.text().lower()
            if all(char in item_text for char in filter_text):
                item.setHidden(False)
            else:
                item.setHidden(True)

    def get_selected_item(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            return selected_items[0].text()
        return None