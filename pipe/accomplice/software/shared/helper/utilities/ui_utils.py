from PySide2 import QtWidgets, QtCore

class FilterableList(QtWidgets.QDialog):
    def filter_items(self):
        filter_text = self.filter_field.text().lower()
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            item_text = item.text().lower()
            if all(char in item_text for char in filter_text):
                item.setHidden(False)
            else:
                item.setHidden(True)


class ListWithFilter(FilterableList):
    def __init__(self, title:str, items:list, accept_button_name = "OK", cancel_button_name="Cancel", list_label=None, include_filter_field=True, parent=None):
        super(ListWithFilter, self).__init__(parent)
        self.setWindowTitle(title)
        
        self.resize(500, 600)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        if list_label is not None:
            assert isinstance(list_label, str)
            self.list_label = QtWidgets.QLabel(list_label)
            layout.addWidget(self.list_label)
        
        if include_filter_field:
            self.filter_field = QtWidgets.QLineEdit()
            self.filter_field.setPlaceholderText("Type here to filter...")
            layout.addWidget(self.filter_field)

        # List box
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(items)
        layout.addWidget(self.list_widget)

        # OK and Cancel buttons
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)

        # Connect signals
        if include_filter_field:
            self.filter_field.textChanged.connect(self.filter_items)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.set_button_names(accept_button_name, cancel_button_name)

    def set_button_names(self, ok_name="OK", cancel_name="Cancel"):
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setText(ok_name)
        self.buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText(cancel_name)

    def get_selected_item(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            return selected_items[0].text()
        return None



class ListWithCheckboxFilter(FilterableList):
    def __init__(self, title: str, items: list, accept_button_name="OK", cancel_button_name="Cancel", list_label=None, include_filter_field=True, parent=None, items_checked_by_default=False):
        super(ListWithCheckboxFilter, self).__init__(parent)
        self.setWindowTitle(title)

        self.resize(500, 600)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        if list_label is not None:
            self.list_label = QtWidgets.QLabel(list_label)
            layout.addWidget(self.list_label)

        if include_filter_field:
            self.filter_field = QtWidgets.QLineEdit()
            self.filter_field.setPlaceholderText("Type here to filter...")
            layout.addWidget(self.filter_field)

        # Select All Checkbox
        self.select_all_checkbox = QtWidgets.QCheckBox("Select All Visible")
        self.select_all_checkbox.stateChanged.connect(self.select_all_items)
        layout.addWidget(self.select_all_checkbox)

        # List box with checkboxes
        self.list_widget = QtWidgets.QListWidget()
        for item_text in items:
            item = QtWidgets.QListWidgetItem(item_text)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked if items_checked_by_default else QtCore.Qt.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # OK and Cancel buttons
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)

        # Connect signals
        if include_filter_field:
            self.filter_field.textChanged.connect(self.filter_items)
        
        if items_checked_by_default:
            self.select_all_checkbox.setCheckState(QtCore.Qt.Checked)


        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.set_button_names(accept_button_name, cancel_button_name)

    def set_button_names(self, ok_name="OK", cancel_name="Cancel"):
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setText(ok_name)
        self.buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText(cancel_name)
    
    def select_all_items(self):
        check_state = self.select_all_checkbox.checkState()
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if not item.isHidden():
                item.setCheckState(check_state)

    def get_selected_items(self):
        selected_items = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                selected_items.append(item.text())
        return selected_items

class InfoDialog(QtWidgets.QDialog):
    def __init__(self, dialog_title, dialog_message, include_cancel_button = False, parent=None):
        super(InfoDialog, self).__init__(parent)
        self.setWindowTitle(dialog_title)
        
        layout = QtWidgets.QVBoxLayout()

        message_label = QtWidgets.QLabel(dialog_message)  # Create a label for the message
        layout.addWidget(message_label)  # Add the label to the layout

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        if include_cancel_button:
            cancel_button = QtWidgets.QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            layout.addWidget(cancel_button)

        self.setLayout(layout)


class TextEntryDialog(QtWidgets.QDialog):
    def __init__(self, dialog_title, dialog_message, parent=None, is_password=False):
        super(TextEntryDialog, self).__init__(parent)
        self.setWindowTitle(dialog_title)
        
        layout = QtWidgets.QVBoxLayout()

        message_label = QtWidgets.QLabel(dialog_message)  # Create a label for the message
        layout.addWidget(message_label)  # Add the label to the layout

        self.text_entry = QtWidgets.QLineEdit()
        layout.addWidget(self.text_entry)
        if is_password:
            self.text_entry.setEchoMode(QtWidgets.QLineEdit.Password)

        # OK and Cancel buttons
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.setLayout(layout)

    def get_text_entry(self):
        text_entry = self.text_entry.text()
        return text_entry
