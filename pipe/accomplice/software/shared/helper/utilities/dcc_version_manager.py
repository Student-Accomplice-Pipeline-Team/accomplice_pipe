from PySide2 import QtWidgets
import time
from abc import ABC, abstractmethod
from pipe.shared.versions import VersionManager

class DCCVersionManager(ABC):
    def __init__(self):
        my_path = self.get_my_path()
        if not my_path:
            QtWidgets.QMessageBox.warning(None, 'No File Open', 'No file is currently open. Open a file and try again.')
            raise Exception("No file is currently open. Open a file and try again.")
        self.vm = VersionManager(my_path)

    @abstractmethod
    def get_my_path(self):
        raise NotImplementedError("Must be implemented in subclass")
    
    @abstractmethod
    def open_file(self):
        raise NotImplementedError("Must be implemented in subclass")

    @abstractmethod
    def check_for_unsaved_changes_and_inform_user(self):
        """
        Checks if the current file has unsaved changes and informs the user.

        Returns:
            bool: True if there are unsaved changes, False otherwise.
        """
        raise NotImplementedError("Must be implemented in subclass")

    def save_new_version(self):
        if self.check_for_unsaved_changes_and_inform_user():
            return

        self.vm.save_new_version()
        QtWidgets.QMessageBox.information(None, 'Version Saved', 'A new version has been saved.')

    def show_current_version(self):
        current_version = self.vm.get_current_version_number()
        QtWidgets.QMessageBox.information(None, 'Current Version', f'The current version is {current_version}.')

    def switch_version_ui(self):
        version_table = self.vm.get_version_table()

        # Sort the version table by timestamp
        version_table_sorted = sorted(version_table, key=lambda x: x[2])

        current_version_number = self.vm.get_current_version_number()

        if hasattr(self, 'versionSwitchWindow') and self.versionSwitchWindow:
            self.versionSwitchWindow.close()

        self.versionSwitchWindow = QtWidgets.QWidget()
        self.versionSwitchWindow.setWindowTitle("Switch to Version (Current Version: " + str(current_version_number) + ")")
        layout = QtWidgets.QVBoxLayout(self.versionSwitchWindow)

        # Create a table widget with an extra column for the buttons
        table = QtWidgets.QTableWidget()
        table.setColumnCount(4)  # Increase column count to include the switch buttons
        table.setHorizontalHeaderLabels(['Version', 'Date Modified', 'Note', ''])
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        for row, (file, version_number, timestamp, note) in enumerate(version_table_sorted):
            table.insertRow(table.rowCount())
            timestamp_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

            # Set items for each cell in the row
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(version_number)))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(timestamp_readable))
            table.setItem(row, 2, QtWidgets.QTableWidgetItem(note))

            # Add a button for switching versions in the fourth column
            btn = QtWidgets.QPushButton('Switch')
            btn.clicked.connect(lambda checked=False, vn=version_number: self.switch_to_selected_version(vn))
            table.setCellWidget(row, 3, btn)  # Add the button as a widget to the fourth column

        # Resize columns to fit contents and ensure the window starts with an adequate size
        table.resizeColumnsToContents()
        # table.horizontalHeader().setStretchLastSection(True)  # Stretch the last column to fill the remaining space
        self.versionSwitchWindow.setMinimumSize(900, 400)  # Set a minimum size for the window

        # Add table to the layout
        layout.addWidget(table)
        self.versionSwitchWindow.show()

    def switch_to_selected_version(self, version_number):
        if self.check_for_unsaved_changes_and_inform_user():
            return

        if hasattr(self, 'versionSwitchWindow') and self.versionSwitchWindow:
            self.versionSwitchWindow.close()

        self.vm.switch_to_version(version_number)

        # Open the file in Maya
        self.open_file()
        QtWidgets.QMessageBox.information(None, 'Version Switched', f'Switched to version {version_number}.')

    def edit_version_note(self):
        current_version = self.vm.get_current_version_number()
        existing_note = self.vm.get_note_for_version(current_version)

        text, ok = QtWidgets.QInputDialog.getText(None, 'Edit Note', f'Enter Note for Version {current_version}:', text=existing_note)

        if ok:
            new_note = text
            self.vm.set_note_for_version(current_version, new_note)