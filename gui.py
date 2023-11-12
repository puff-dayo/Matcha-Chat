import json
import os
import sys

from PySide6.QtCore import QDateTime, QObject, Signal, Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                               QTextEdit, QLineEdit, QPushButton, QGroupBox,
                               QFormLayout, QSpinBox, QLabel, QFileDialog, QMessageBox)

import func
import model_dl
import cuda_dl


class ParameterController(QObject):
    thread_count_changed = Signal(int)
    cache_size_changed = Signal(int)
    n_predict_change = Signal(int)

parameter_controller = ParameterController()

card_dir = os.path.join(os.getcwd(), 'character_cards')
os.makedirs(card_dir, exist_ok=True)


class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self.parent().on_ctrl_enter_pressed()


class ChatUI(QWidget):

    def __init__(self):
        super().__init__()
        self.sys_prompt = ("Fluffy, the cute 16 years old cat girl maid, exudes irresistible charm with her wagging "
                           "tail, perky cat ears, and revealing outfit. She likes talking with her mistress about "
                           "everything. She showers her mistress with affection through gentle rubs, "
                           "purrs of contentment, and erotic pleasure. She brings joy and companionship, "
                           "forever cherished by her adoring mistress.\nPairs of parentheses are used to indicate "
                           "actions.\nHere is a transcript of a never ending text dialog, where Mistress interacts "
                           "with her cat girl Fluffy.\nFluffy:Welcome home, my mistress. (lifts her "
                           "mini-skirt)\nMistress:")
        self.prompt = ""
        self.next_prompt = ""
        self.user_name = 'Mistress'
        self.ai_name = 'Fluffy'
        self.next_predict = 512
        self.if_first = False
        self.llamaurl = 'https://github.com/ggerganov/llama.cpp/releases/download/b1485/llama-b1485-bin-win-openblas-x64.zip'
        self.cudallamaurl = 'https://github.com/ggerganov/llama.cpp/releases/download/b1485/llama-b1485-bin-win-cublas-cu11.7.1-x64.zip'
        self.cudakiturl = 'https://github.com/ggerganov/llama.cpp/releases/download/b1485/cudart-llama-bin-win-cu11.7.1-x64.zip'
        self.init_ui()

    def init_ui(self):

        hbox = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        left_layout.addWidget(self.chat_display)

        self.input_line = CustomTextEdit()
        self.input_line.setMinimumHeight(50)
        self.input_line.setMaximumHeight(100)
        self.input_line.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.addWidget(self.input_line)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.send_button = QPushButton("Send")
        self.send_button.setFixedWidth(80)
        self.send_button.clicked.connect(self.send_message)
        clear_button = QPushButton("Clear")
        clear_button.setFixedWidth(80)
        button_layout.addWidget(QLabel('Use Ctrl+Enter to send'))
        button_layout.addWidget(clear_button)
        button_layout.addWidget(self.send_button)
        clear_button.clicked.connect(self.clear_message)

        left_layout.addLayout(button_layout)

        right_layout = QVBoxLayout()

        group_box = QGroupBox(f"System")
        group_layout = QFormLayout()

        self.button1 = QPushButton("1. Download llama.cpp")
        self.button1.clicked.connect(lambda: self.llamacpp_dler)
        group_layout.addRow(self.button1)

        self.button2 = QPushButton("2. Download a model")
        self.button2.clicked.connect(lambda: self.model_dler())
        group_layout.addRow(self.button2)

        self.button3 = QPushButton("3. Launch Llama server")
        self.button3.clicked.connect(self.start_server)
        group_layout.addRow(self.button3)

        group_layout.addRow(QLabel('Optional:'))
        self.button4 = QPushButton("1. Enable GPU acceleration")
        self.button4.clicked.connect(self.check_gpu)
        group_layout.addRow(self.button4)

        group_box.setLayout(group_layout)
        right_layout.addWidget(group_box)

        group_box2 = QGroupBox("Model")
        group_layout2 = QFormLayout()

        self.thread_count_spinbox = QSpinBox()
        self.thread_count_spinbox.setMinimum(1)
        self.thread_count_spinbox.setMaximum(32)
        self.thread_count_spinbox.setValue(16)
        group_layout2.addRow("Thread count:", self.thread_count_spinbox)

        self.content_size_spinbox = QSpinBox()
        self.content_size_spinbox.setMinimum(1024)
        self.content_size_spinbox.setMaximum(8192)
        self.content_size_spinbox.setValue(4096)
        group_layout2.addRow("Content size:", self.content_size_spinbox)

        self.gpu_layer_spinbox = QSpinBox()
        self.gpu_layer_spinbox.setMinimum(0)
        self.gpu_layer_spinbox.setMaximum(1024)
        self.gpu_layer_spinbox.setValue(10)
        group_layout2.addRow("GPU layers:", self.gpu_layer_spinbox)

        self.n_pridict_spinbox = QSpinBox()
        self.n_pridict_spinbox.setMinimum(128)
        self.n_pridict_spinbox.setMaximum(4096)
        self.n_pridict_spinbox.setValue(512)
        group_layout2.addRow("Next predict:", self.n_pridict_spinbox)

        self.thread_count_spinbox.valueChanged.connect(parameter_controller.thread_count_changed.emit)
        self.content_size_spinbox.valueChanged.connect(parameter_controller.cache_size_changed.emit)
        self.n_pridict_spinbox.valueChanged.connect(parameter_controller.n_predict_change.emit)

        group_box2.setLayout(group_layout2)
        right_layout.addWidget(group_box2)

        group_box3 = QGroupBox("Character")
        group_layout3 = QFormLayout()

        load_chara_card = QPushButton("Load charactor card")
        load_chara_card.clicked.connect(self.load_from_json)
        group_layout3.addRow(load_chara_card)
        save_chara_card = QPushButton("Save charactor card")
        save_chara_card.clicked.connect(self.save_to_json)
        group_layout3.addRow(save_chara_card)

        self.toggle_button = QPushButton("...")
        self.toggle_button.clicked.connect(self.toggle_visibility)
        group_layout3.addRow(self.toggle_button)

        self.sender_name_line_edit = QLineEdit()
        group_layout3.addRow("User Name:", self.sender_name_line_edit)
        self.sender_name_line_edit.setText(self.user_name)
        self.sender_name_line_edit.textChanged.connect(self.on_user_name_changed)

        self.ai_name_line_edit = QLineEdit()
        group_layout3.addRow("AI Name:", self.ai_name_line_edit)
        self.ai_name_line_edit.setText(self.ai_name)
        self.ai_name_line_edit.textChanged.connect(self.on_ai_name_changed)

        self.system_prompt_text_edit = QTextEdit()
        self.sys_tip = QLabel("System Prompt:")
        group_layout3.addRow(self.sys_tip)
        group_layout3.addRow(self.system_prompt_text_edit)
        self.system_prompt_text_edit.setText(self.sys_prompt)
        self.system_prompt_text_edit.textChanged.connect(self.on_sys_prompt_changed)

        self.sender_name_line_edit.setReadOnly(True)
        self.ai_name_line_edit.setReadOnly(True)
        self.sys_tip.setVisible(False)
        self.system_prompt_text_edit.setVisible(False)

        group_box3.setLayout(group_layout3)
        right_layout.addWidget(group_box3)

        hbox.addLayout(left_layout, 5)
        hbox.addLayout(right_layout, 2)

        self.setWindowTitle("Matcha Chat")
        self.setGeometry(300, 300, 800, 600)
        self.checkFile()

    def on_ctrl_enter_pressed(self):
        self.send_message()

    def check_gpu(self):
        if self.detect_file('./pkgs', 'server.exe'):
            if not self.detect_file('./pkgs', 'openblas.dll'):
                self.button4.setText('1. Enabled GPU acceleration[√]')
                self.checkFile()
            else:
                for filename in os.listdir('./pkgs'):
                    if os.path.isfile(os.path.join('./pkgs', filename)):
                        new_filename = filename + ".bak"
                        os.rename(os.path.join('./pkgs', filename), os.path.join('./pkgs', new_filename))
                        print(f"Renamed {filename} to {new_filename}")
                self.cuda_llamacpp_dler()
                self.button4.setText('1. Enabled GPU acceleration[√]')
                self.checkFile()
            self.checkFile()
        else:
            self.cuda_llamacpp_dler()
            self.button4.setText('1. Enabled GPU acceleration[√]')
            self.checkFile()

    def start_server(self):
        func.run_server(self.thread_count_spinbox.value(), self.content_size_spinbox.value(),
                        self.gpu_layer_spinbox.value())
        self.button3.setText('3. Launched Llama server[√]')
        self.content_size_spinbox.setReadOnly(True)
        self.thread_count_spinbox.setReadOnly(True)
        self.gpu_layer_spinbox.setReadOnly(True)

    def toggle_visibility(self):
        is_visible = self.sender_name_line_edit.isReadOnly()
        self.sender_name_line_edit.setReadOnly(not is_visible)
        self.ai_name_line_edit.setReadOnly(not is_visible)
        self.sys_tip.setVisible(is_visible)
        self.system_prompt_text_edit.setVisible(is_visible)

    def on_ai_name_changed(self, text):
        self.ai_name = text

    def on_user_name_changed(self, text):
        self.user_name = text

    def get_text_edit_content(self):
        return self.system_prompt_text_edit.toPlainText()

    def on_sys_prompt_changed(self):
        self.sys_prompt = self.get_text_edit_content()

    def llamacpp_dler(self):
        func.get_llama(self.llamaurl)
        self.checkFile()

    def cuda_llamacpp_dler(self):

        cuda_dl.DownloadDialog(urls=[self.cudallamaurl, self.cudakiturl],
                               dests=["llama-b1485-bin-win-cublas-cu11.7.1-x64.zip",
                                      "cudart-llama-bin-win-cu11.7.1-x64.zip"]).exec()
        self.checkFile()

    def detect_file(self, folder, name):

        if not os.path.exists(folder):
            print(f"The folder {folder} does not exist.")
            return False

        for filename in os.listdir(folder):
            if filename == name:
                return True
        return False

    def checkFile(self):
        if self.detect_file('./pkgs', 'server.exe'):
            self.button1.setText("1. Downloaded llama.cpp[√]")
        if self.detect_file('./models', 'Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf'):
            self.button2.setText("2. Downloaded model[√]")
        if self.detect_file('./pkgs', 'server.exe'):
            if not self.detect_file('./pkgs', 'openblas.dll'):
                self.button4.setText('1. Enabled GPU acceleration[√]')

    def clear_message(self):
        self.ai_name = self.ai_name_line_edit.text()
        self.user_name = self.sender_name_line_edit.text()
        self.sys_prompt = self.system_prompt_text_edit.toPlainText()
        self.if_first = False
        self.chat_display.setText('')

    def model_dler(self):
        file_url = 'https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGUF/resolve/main/Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf'
        destination_path = './models/Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf'

        self.download_dialog = model_dl.DownloadDialog(file_url, destination_path, self)
        self.download_dialog.exec()

        self.checkFile()

    def append_message(self, sender, message):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        color = "#FF9999" if sender == "Mistress" else "#99CCFF"

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        time_format = QTextCharFormat()
        time_format.setForeground(QColor(color))
        time_format.setFontWeight(QFont.Bold)
        cursor.insertText(f"{sender} {current_time}:\n", time_format)

        text_format = QTextCharFormat()
        cursor.insertText(f"{message}\n\n", text_format)

        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        self.chat_display.ensureCursorVisible()

    def send_message(self):
        message = self.input_line.toPlainText()
        if message:
            self.setWindowTitle("Matcha Chat (Generating, plz wait....)")
            self.append_message(self.user_name, message)

            custom_stop_sequence = [self.user_name + ':', self.user_name + ': ']

            if not self.if_first:
                self.prompt = self.sys_prompt + message + '\n' + self.ai_name + ':'
                print('1:' + self.prompt)
                response_content = func.get_response(self.prompt, custom_stop_sequence, self.n_pridict_spinbox.value())
                self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
                self.if_first = True
                if response_content.endswith("\n"):
                    self.next_prompt = self.prompt + response_content + self.user_name + ":"
                else:
                    self.next_prompt = self.prompt + response_content + "\n" + self.user_name + ":"
            else:
                self.next_prompt = self.next_prompt + message + '\n' + self.ai_name + ':'
                print('2:' + self.next_prompt)
                response_content = func.get_response(self.next_prompt, custom_stop_sequence,
                                                     self.n_pridict_spinbox.value())
                self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
                if response_content.endswith("\n"):
                    self.next_prompt = self.next_prompt + response_content + self.user_name + ":"
                else:
                    self.next_prompt = self.next_prompt + response_content + "\n" + self.user_name + ":"

            self.input_line.clear()
            self.setWindowTitle("Matcha Chat")

    def save_to_json(self):

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            data = {
                'ai_name': self.ai_name,
                'user_name': self.user_name,
                'sys_prompt': self.sys_prompt
            }
            try:
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
                QMessageBox.information(self, "Success", "Data saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def load_from_json(self):

        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    self.ai_name = data.get('ai_name', '')
                    self.user_name = data.get('user_name', '')
                    self.sys_prompt = data.get('sys_prompt', '')

                    self.ai_name_line_edit.setText(self.ai_name)
                    self.sender_name_line_edit.setText(self.user_name)
                    self.system_prompt_text_edit.setText(self.sys_prompt)
                QMessageBox.information(self, "Success", "Data loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")


def on_close():
    print('Server shutdown.')
    os.system('taskkill /f /im server.exe')


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('./icon.png'))
    app.setStyle('Fusion')
    app.aboutToQuit.connect(on_close)
    chat_ui = ChatUI()
    chat_ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
