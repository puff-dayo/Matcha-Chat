import datetime
import json
from collections import OrderedDict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog, QLineEdit,
                               QTextEdit, QLabel, QVBoxLayout, QFormLayout, QMessageBox, QDialogButtonBox, QHBoxLayout,
                               QPushButton, QInputDialog, QListWidgetItem, QListWidget)


class MemoryManager:
    def __init__(self, filename="memories.json"):
        self.filename = filename
        try:
            with open(filename, 'r') as file:
                self.memories = json.load(file, object_pairs_hook=OrderedDict)
        except FileNotFoundError:
            self.memories = OrderedDict()

    def add_memory(self, content):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory_entry = {"content": content, "timestamp": timestamp}
        self.memories[timestamp] = memory_entry
        return timestamp

    def save(self):
        with open(self.filename, 'w') as file:
            json.dump(self.memories, file, indent=4)

    def get_memories_string(self):
        all_memories_string = ""
        for timestamp, _memory in self.memories.items():
            formatted_memory = f"{timestamp} - {_memory['content']}\n"
            all_memories_string += formatted_memory
        return all_memories_string.strip()

    def get_memories(self):
        return list(self.memories.values())

    def delete_memory(self, timestamp):
        if timestamp in self.memories:
            del self.memories[timestamp]
            self.save()

    def modify_memory(self, timestamp, modified_content):
        if timestamp in self.memories:
            self.memories[timestamp]['content'] = modified_content
            self.save()


# class MemoryDialog(QDialog):
#     def __init__(self, _memory_manager, parent=None):
#         super().__init__(parent)
#         self.memory_manager = _memory_manager
#         self.setWindowTitle("Memory Manager")
#
#         self.content_edit = QLineEdit()
#         self.timestamp_label = QLabel()
#         self.timestamp_label.setAlignment(Qt.AlignRight)
#         self.memory_text = QTextEdit()
#         self.memory_text.setReadOnly(True)
#
#         self.add_button = QPushButton("Add")
#         self.add_button.clicked.connect(self.add_memory)
#
#         self.delete_button = QPushButton("Delete")
#         self.delete_button.clicked.connect(self.delete_memory)
#
#         self.modify_button = QPushButton("Modify")
#         self.modify_button.clicked.connect(self.modify_memory)
#
#         self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Discard)
#         self.button_box.accepted.connect(self.save_memory)
#         self.button_box.rejected.connect(self.reject)
#
#         form_layout = QFormLayout()
#         form_layout.addRow("Content:", self.content_edit)
#         form_layout.addRow("Timestamp:", self.timestamp_label)
#
#         button_layout = QHBoxLayout()
#         button_layout.addWidget(self.add_button)
#         button_layout.addWidget(self.delete_button)
#         button_layout.addWidget(self.modify_button)
#
#         main_layout = QVBoxLayout()
#         main_layout.addLayout(form_layout)
#         main_layout.addWidget(self.memory_text)
#         main_layout.addLayout(button_layout)
#         main_layout.addWidget(self.button_box)
#
#         self.setLayout(main_layout)
#
#         self.show_memories()
#
#     def show_memories(self):
#         all_memories = self.memory_manager.get_memories()
#         memory_strings = [f"{memory['timestamp']} - {memory['content']}" for memory in all_memories]
#         self.memory_text.setText("\n".join(memory_strings))
#
#     def add_memory(self):
#         content = self.content_edit.text()
#         if not content:
#             QMessageBox.warning(self, "Warning", "Memory content cannot be empty.")
#             return
#         self.memory_manager.add_memory(content)
#         self.show_memories()
#
#     def delete_memory(self):
#         selected_text = self.memory_text.textCursor().selectedText()
#         if not selected_text:
#             QMessageBox.warning(self, "Warning", "Please select a memory to delete.")
#             return
#
#         timestamp = selected_text.split(" - ", 1)[0]
#
#         self.memory_manager.delete_memory(timestamp)
#         self.show_memories()
#
#     def modify_memory(self):
#         selected_text = self.memory_text.textCursor().selectedText()
#         if not selected_text:
#             QMessageBox.warning(self, "Warning", "Please select a memory to modify.")
#             return
#         timestamp = selected_text.split(" - ", 1)[0]
#
#         modified_content, okPressed = QInputDialog.getText(self, "Modify Memory", "Enter modified content:")
#         if okPressed:
#             self.memory_manager.modify_memory(timestamp, modified_content)
#             self.show_memories()
#
#     def save_memory(self):
#         content = self.content_edit.text()
#         if not content:
#             QMessageBox.warning(self, "Warning", "Memory content cannot be empty.")
#             return
#         timestamp = self.memory_manager.add_memory(content)
#         self.timestamp_label.setText(timestamp)
#         self.show_memories()


class MemoryDialog(QDialog):
    def __init__(self, memory_manager, parent=None):
        super().__init__(parent)
        self.memory_manager = memory_manager
        self.setWindowTitle("Memory Manager")

        self.content_edit = QLineEdit()
        self.timestamp_label = QLabel()
        self.timestamp_label.setAlignment(Qt.AlignRight)

        self.memory_list = QListWidget()
        self.memory_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.memory_list.itemSelectionChanged.connect(self.update_memory_text)

        self.memory_text = QTextEdit()
        self.memory_text.setReadOnly(True)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_memory)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_memory)

        self.modify_button = QPushButton("Modify")
        self.modify_button.clicked.connect(self.modify_memory)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Discard)
        self.button_box.accepted.connect(self.save_memory)
        self.button_box.rejected.connect(self.reject)

        form_layout = QFormLayout()
        form_layout.addRow("Content:", self.content_edit)
        form_layout.addRow("Timestamp:", self.timestamp_label)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.memory_list)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.memory_text)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.modify_button)

        add_content_layout = QHBoxLayout()
        add_content_label = QLabel("Add Memory:")
        add_content_layout.addWidget(add_content_label)
        add_content_layout.addWidget(self.content_edit)

        right_layout.addLayout(add_content_layout)
        right_layout.addLayout(button_layout)
        right_layout.addWidget(self.button_box)

        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

        self.show_memories()

    def show_memories(self):
        self.memory_list.clear()
        self.memory_text.clear()
        all_memories = self.memory_manager.get_memories()
        for memory in all_memories:
            timestamp = memory['timestamp']
            content = memory['content']
            item = QListWidgetItem(timestamp)
            self.memory_list.addItem(item)

    def update_memory_text(self):
        selected_items = self.memory_list.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            timestamp = selected_item.text()
            all_memories = self.memory_manager.get_memories()
            for memory in all_memories:
                if memory['timestamp'] == timestamp:
                    content = memory['content']
                    self.memory_text.setText(f"{timestamp} - {content}")
                    break

    def add_memory(self):
        content = self.content_edit.text()
        if not content:
            QMessageBox.warning(self, "Warning", "Memory content cannot be empty.")
            return
        self.memory_manager.add_memory(content)
        self.show_memories()
        self.update_memory_text()

    def delete_memory(self):
        selected_items = self.memory_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select one or more memories to delete.")
            return

        timestamps_to_delete = [item.text() for item in selected_items]

        for timestamp in timestamps_to_delete:
            self.memory_manager.delete_memory(timestamp)

        self.show_memories()
        self.update_memory_text()

    def modify_memory(self):
        selected_items = self.memory_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a memory to modify.")
            return

        selected_item = selected_items[0]
        timestamp = selected_item.text()

        modified_content, okPressed = QInputDialog.getText(self, "Modify Memory", "Enter modified content:")
        if okPressed:
            self.memory_manager.modify_memory(timestamp, modified_content)
            self.show_memories()
            self.update_memory_text()

    def save_memory(self):
        content = self.content_edit.text()
        if not content:
            QMessageBox.warning(self, "Warning", "Memory content cannot be empty.")
            return
        self.memory_manager.add_memory(content)
        self.show_memories()
        self.update_memory_text()


if __name__ == "__main__":
    app = QApplication([])

    memory_manager = MemoryManager()

    main_window = QMainWindow()
    main_window.setWindowTitle("Main Window")
    main_window.show()

    memory_dialog = MemoryDialog(memory_manager, main_window)
    memory_dialog.show()

    app.exec()
