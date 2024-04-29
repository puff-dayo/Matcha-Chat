import datetime
import json
from collections import OrderedDict

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog, QLineEdit,
                               QTextEdit, QLabel, QVBoxLayout, QFormLayout, QDialogButtonBox, QHBoxLayout,
                               QPushButton, QInputDialog, QListWidgetItem, QListWidget, QWidget)
import services.windows_api_handler
from components.custom_message_box import CustomMessageBox
from components.custom_titlebar import CustomTitleBar


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


class MemoryWindow(QMainWindow):
    def __init__(self, _memory_manager, parent=None):
        super().__init__(parent)

        self.messagebox = None
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        self.init_width = int(screen_width * 0.42)
        self.init_height = int(screen_height * 0.72)
        self.resize(self.init_width, self.init_height)

        self.move(int((screen_width - self.init_width) / 2), int((screen_height - self.init_height) / 2))

        self.memory_manager = _memory_manager

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowMaximizeButtonHint)
        self.titleBar = CustomTitleBar(self, custom_title="Matcha Chat 2 - Memory Manager")
        self.setMenuWidget(self.titleBar)
        self.setWindowTitle("Memory Manager")

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        self.setStyleSheet("background:transparent")
        self.windowEffect = services.windows_api_handler.WindowEffect()
        self.windowEffect.setAcrylicEffect(int(self.winId()), gradientColor='00101080')

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.content_edit = QLineEdit()
        palette = self.content_edit.palette()
        palette.setColor(QPalette.Highlight, QColor("#5bb481"))
        self.content_edit.setPalette(palette)

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
        # self.button_box.rejected.connect(self.reject)

        for button in [self.add_button, self.delete_button, self.modify_button]:
            button_style = """
                    QPushButton {
                        background-color: #599e5e;
                        border: none;
                        padding-top: 2px;
                        padding-right: 10px;
                        padding-bottom: 2px;
                        padding-left: 10px;
                    }

                    QPushButton:hover {
                        background-color: #2b8451;
                    }
                    """
            button.setStyleSheet(button_style)

        form_layout = QFormLayout()
        form_layout.addRow("Content:", self.content_edit)
        form_layout.addRow("Timestamp:", self.timestamp_label)

        main_layout = QHBoxLayout(central_widget)
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

        hey_stylesheet = """
                QTextEdit, QLineEdit {
                    border: 2px solid transparent;
                    border-radius: 0px;
                }
                QTextEdit:focus, QLineEdit:focus {
                    border: 2px solid #599e5e;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: lightgray;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background-color: #599e5e;
                    border-radius: 0px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    background: none;
                }
                """
        for widget in [self.content_edit, self.memory_text]:
            widget.setStyleSheet(hey_stylesheet)

        self.memory_list.setStyleSheet("""
                    QListWidget::item:selected {
                        background-color: #599e5e;
                    }
                    
                    QScrollBar:vertical {
                        border: 0px solid grey;
                        background: #f1f1f1;
                        width: 10px;
                        margin: 0 0 0 0;
                    }
                    
                    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                        border: 2px solid grey;
                        background: #8f8f8f;
                        height: 20px;
                        subcontrol-position: top;
                        subcontrol-origin: margin;
                    }
                    
                    QScrollBar::add-line:vertical {
                        subcontrol-position: bottom;
                    }
                    
                    QScrollBar::handle:vertical {
                        background: #599e5e;
                        min-height: 20px;
                    }
                    
                    QScrollBar::handle:vertical:hover {
                        background: #599e5e;
                    }
                    
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                        background: none;
                    }
                """)

        self.show_memories()
        self.content_edit.setFocus()

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
            self.messagebox = CustomMessageBox(title="Warning", text="Memory content cannot be empty.")
            self.messagebox.show()
            return
        self.memory_manager.add_memory(content)
        self.show_memories()
        self.update_memory_text()

    def delete_memory(self):
        selected_items = self.memory_list.selectedItems()
        if not selected_items:
            self.messagebox = CustomMessageBox(title="Warning", text="Memory content cannot be empty.")
            self.messagebox.show()
            return

        timestamps_to_delete = [item.text() for item in selected_items]

        for timestamp in timestamps_to_delete:
            self.memory_manager.delete_memory(timestamp)

        self.show_memories()
        self.update_memory_text()

    def modify_memory(self):
        selected_items = self.memory_list.selectedItems()
        if not selected_items:
            self.messagebox = CustomMessageBox(title="Warning", text="Please select a memory to modify.")
            self.messagebox.show()
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
            self.messagebox = CustomMessageBox(title="Warning", text="Memory content cannot be empty.")
            self.messagebox.show()
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

    memory_dialog = MemoryWindow(memory_manager, main_window)
    memory_dialog.show()

    app.exec()
