import base64
import json
import os
import sys
import time

from PySide6.QtCore import QDateTime, QObject, Signal, Qt, QSize, QByteArray, QBuffer
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QIcon, QPalette, QImage, QImageReader
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                               QTextEdit, QLineEdit, QPushButton, QGroupBox,
                               QFormLayout, QSpinBox, QLabel, QFileDialog, QMessageBox, QDoubleSpinBox, QFrame)

import cuda_dl
import func
import llama_dl
import llava_service
import model_dl
import cap_dl


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

        temp_dir = os.path.join(os.getcwd(), 'temp')
        for filename in os.listdir(temp_dir):
            if filename.endswith(".log"):
                file_path = os.path.join(temp_dir, filename)
                os.remove(file_path)

        self.init_width = 800
        self.init_height = 600
        self.resize(self.init_width, self.init_height)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

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
        self.llamaurl = 'https://github.com/ggerganov/llama.cpp/releases/download/b1627/llama-b1627-bin-win-openblas-x64.zip'
        self.cudallamaurl = 'https://github.com/ggerganov/llama.cpp/releases/download/b1627/llama-b1627-bin-win-cublas-cu11.7.1-x64.zip'
        self.cudakiturl = 'https://github.com/ggerganov/llama.cpp/releases/download/b1627/cudart-llama-bin-win-cu11.7.1-x64.zip'

        self.is_vision_enabled = False
        self.is_to_send_image = False
        self.image_path = ""

        self.init_ui()

    def init_ui(self):

        hbox = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        left_layout.addWidget(self.chat_display)

        tool_bar = QHBoxLayout()

        self.photo_button = QPushButton()
        self.photo_button.setIcon(QIcon('./icons/photo.png'))
        self.photo_button.setIconSize(QSize(24, 24))
        self.photo_button.clicked.connect(self.on_photo_clicked)
        self.photo_button.setToolTip("Send an image into chat.")

        download_button = QPushButton()
        download_button.setIcon(QIcon('./icons/download.png'))
        download_button.setIconSize(QSize(24, 24))
        download_button.clicked.connect(self.on_download_clicked)
        download_button.setToolTip("Save current chat history as a file.")

        undo_button = QPushButton()
        undo_button.setIcon(QIcon('./icons/undo.png'))
        undo_button.setIconSize(QSize(24, 24))
        undo_button.clicked.connect(self.on_undo_clicked)
        undo_button.setToolTip("Undo last sent message.")

        delete_button = QPushButton()
        delete_button.setIcon(QIcon('./icons/delete.png'))
        delete_button.setIconSize(QSize(24, 24))
        delete_button.setToolTip("Clear chat history.")
        delete_button.clicked.connect(self.clear_message)

        settings_button = QPushButton()
        settings_button.setIcon(QIcon('./icons/settings.png'))
        settings_button.setIconSize(QSize(24, 24))
        settings_button.setToolTip("Show or hide setting panel.")
        settings_button.clicked.connect(self.toggle_settings)

        self.photo_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        download_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        undo_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        delete_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        settings_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")

        tool_bar.addWidget(self.photo_button)
        tool_bar.addWidget(download_button)
        tool_bar.addWidget(undo_button)
        tool_bar.addWidget(delete_button)
        tool_bar.addWidget(settings_button)
        tool_bar.addStretch()

        left_layout.addLayout(tool_bar)

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
        self.send_button.setEnabled(False)
        clear_button = QPushButton("Clear")
        clear_button.setFixedWidth(80)
        button_layout.addWidget(QLabel('Use Ctrl+Enter to send'))
        button_layout.addWidget(clear_button)
        button_layout.addWidget(self.send_button)
        clear_button.clicked.connect(self.clear_message)

        left_layout.addLayout(button_layout)

        self.right_layout = QVBoxLayout()

        self.right_frame = QFrame()
        self.right_frame.setLayout(self.right_layout)

        group_box = QGroupBox(f"System")
        group_layout = QFormLayout()

        self.button1 = QPushButton("1. Download llama.cpp")
        self.button1.clicked.connect(lambda: self.llamacpp_dler())
        group_layout.addRow(self.button1)

        self.button2 = QPushButton("2. Download a model")
        self.button2.clicked.connect(lambda: self.model_dler())
        group_layout.addRow(self.button2)

        self.button3 = QPushButton("3. Launch Llama server")
        self.button3.clicked.connect(self.start_server)
        group_layout.addRow(self.button3)

        label_here = QLabel('Optional downloads')
        label_here.setAlignment(Qt.AlignCenter)
        group_layout.addRow(label_here)
        self.button4 = QPushButton("1. Enable GPU acceleration")
        self.button4.clicked.connect(self.check_gpu)
        group_layout.addRow(self.button4)
        self.buttonC = QPushButton("2. Enable vision ability")
        self.buttonC.clicked.connect(self.check_vision)
        group_layout.addRow(self.buttonC)

        group_box.setLayout(group_layout)
        self.right_layout.addWidget(group_box)

        group_box2 = QGroupBox("Model")
        group_layout2 = QFormLayout()

        self.thread_count_spinbox = QSpinBox()
        self.thread_count_spinbox.setMinimum(1)
        self.thread_count_spinbox.setMaximum(128)
        self.thread_count_spinbox.setValue(16)
        self.thread_count_spinbox.setToolTip("Set the number of threads for processing.\n\nRange: 1-128.")
        group_layout2.addRow("Thread count:", self.thread_count_spinbox)

        self.content_size_spinbox = QSpinBox()
        self.content_size_spinbox.setMinimum(256)
        self.content_size_spinbox.setMaximum(4096)
        self.content_size_spinbox.setValue(4096)
        self.content_size_spinbox.setToolTip(
            "The maximum sequence length that this model might ever be used with.\n\nRange: 256-4096.")
        group_layout2.addRow("Content size:", self.content_size_spinbox)

        self.gpu_layer_spinbox = QSpinBox()
        self.gpu_layer_spinbox.setMinimum(0)
        self.gpu_layer_spinbox.setMaximum(1024)
        self.gpu_layer_spinbox.setValue(0)
        self.gpu_layer_spinbox.setToolTip(
            "This option allows offloading some layers to the GPU for computation.\nGenerally results in increased performance.\n\nNeeds much more RAM.")
        group_layout2.addRow("GPU layers:", self.gpu_layer_spinbox)

        self.n_pridict_spinbox = QSpinBox()
        self.n_pridict_spinbox.setMinimum(-1)
        self.n_pridict_spinbox.setMaximum(8192)
        self.n_pridict_spinbox.setValue(512)
        self.n_pridict_spinbox.setToolTip(
            "Set the maximum number of tokens to predict when generating text.\n\n(-1 = infinity)")
        group_layout2.addRow("Next predict:", self.n_pridict_spinbox)

        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setMinimum(0.001)
        self.temperature_spinbox.setMaximum(10)
        self.temperature_spinbox.setValue(0.95)
        self.temperature_spinbox.setSingleStep(0.05)
        self.temperature_spinbox.setToolTip("Adjust the randomness of the generated text (default: 0.95).")
        group_layout2.addRow("Temperature:", self.temperature_spinbox)

        self.thread_count_spinbox.valueChanged.connect(parameter_controller.thread_count_changed.emit)
        self.content_size_spinbox.valueChanged.connect(parameter_controller.cache_size_changed.emit)
        self.n_pridict_spinbox.valueChanged.connect(parameter_controller.n_predict_change.emit)

        group_box2.setLayout(group_layout2)
        self.right_layout.addWidget(group_box2)

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
        self.right_layout.addWidget(group_box3)

        hbox.addLayout(left_layout, 5)
        hbox.addWidget(self.right_frame, 2)

        self.setWindowTitle("Matcha Chat")
        self.setGeometry(150, 150, 800, 600)
        self.right_frame_width = self.right_frame.sizeHint().width()
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

    def cap_dler(self):
        cap_dl.DownloadDialog().exec()

    def check_vision(self):
        if not self.detect_file('./models/cap', 'pytorch_model.bin'):
            self.buttonC.setText("2. Enable vision ability")
            self.cap_dler()
            self.checkFile()
        else:
            self.buttonC.setText('2. Enabled vision ability[√]')
            self.is_vision_enabled = True
            self.checkFile()

    def on_photo_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select an image", "", "Image (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.is_to_send_image = True
            self.image_path = file_name
            image = QImage(file_name)
            if image.isNull():
                return

            # max_height = 300
            # if image.height() > max_height:
            #     image = image.scaledToHeight(max_height, Qt.SmoothTransformation)
            #
            # buffer = QByteArray()
            # qbuffer = QBuffer(buffer)
            # qbuffer.open(QBuffer.ReadWrite)
            # image.save(qbuffer, "PNG")
            # base64_data = base64.b64encode(buffer.data()).decode()
            #
            # # 在QTextEdit中插入图片
            # image_html = f'<img src="data:image/png;base64,{base64_data}" style="max-height: 300px;">'
            # self.chat_display.append(image_html)

    def on_download_clicked(self):
        print("Download button clicked")

    def on_undo_clicked(self):
        print("Undo button clicked")
        
    def toggle_settings(self):
        is_visible = self.right_frame.isVisible()
        self.right_frame.setVisible(not is_visible)
        if is_visible:
            self.resize(self.width() - self.right_frame_width, self.height())
        else:
            self.resize(self.width() + self.right_frame_width, self.height())

    def check_log_file(self, file):
        if not os.path.exists(os.path.join(os.getcwd(), 'temp') + "/llama_output.log"):
            return False
        with open(f"./temp/{file}_output.log", "r") as file:
            logs = file.read()
            return "all slots are idle and system prompt is empty, clear the KV cache" in logs

    def wait_for_log_message(self, file):
        while not self.check_log_file(file):
            pass

    def start_server(self):
        self.setWindowTitle("Matcha Chat (Launching, plz wait....)")
        func.run_server(self.thread_count_spinbox.value(), self.content_size_spinbox.value(),
                        self.gpu_layer_spinbox.value())
        self.wait_for_log_message('llama')
        self.button3.setText('3. Launched Llama server[√]')
        self.send_button.setEnabled(True)
        self.content_size_spinbox.setReadOnly(True)
        self.thread_count_spinbox.setReadOnly(True)
        self.gpu_layer_spinbox.setReadOnly(True)
        self.setWindowTitle("Matcha Chat")
        self.button3.setEnabled(False)

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
        print("0")
        # func.get_llama(self.llamaurl)
        llama_dl.DownloadDialog(urls=[self.llamaurl],
                                dests=["llama-b1627-bin-win-openblas-x64.zip"]).exec()
        self.checkFile()

    def cuda_llamacpp_dler(self):

        cuda_dl.DownloadDialog(urls=[self.cudallamaurl, self.cudakiturl],
                               dests=["llama-b1627-bin-win-cublas-cu11.7.1-x64.zip",
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
        if self.detect_file('./models', 'llava-v1.5-7b-q4-server.llamafile.exe'):
            self.buttonC.setText('2. Enabled vision ability[√]')
            self.is_vision_enabled = True

    def clear_message(self):
        self.ai_name = self.ai_name_line_edit.text()
        self.user_name = self.sender_name_line_edit.text()
        self.sys_prompt = self.system_prompt_text_edit.toPlainText()
        self.if_first = False
        self.chat_display.setText('')

    def model_dler(self):
        file_url = ('https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGUF/resolve/main/Wizard-Vicuna-7B'
                    '-Uncensored.Q5_K_M.gguf')
        destination_path = './models/Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf'

        self.download_dialog = model_dl.DownloadDialog(file_url, destination_path, self)
        self.download_dialog.exec()

        self.checkFile()

    def append_message(self, sender, message):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        color = "#FF9999" if sender == self.user_name else "#99CCFF"

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        time_format = QTextCharFormat()
        time_format.setForeground(QColor(color))
        time_format.setFontWeight(QFont.Bold)
        cursor.insertText(f"{sender} {current_time}:\n", time_format)

        text_format = QTextCharFormat()
        if self.is_to_send_image:
            cursor.insertText(f"{message}\n", text_format)
            self.is_to_send_image = False
        else:
            cursor.insertText(f"{message}\n\n", text_format)

        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        self.chat_display.ensureCursorVisible()

    def send_message(self):
        message = self.input_line.toPlainText()
        if message:
            if self.is_to_send_image:
                self.setWindowTitle("Matcha Chat (Generating, plz wait....)")
                self.append_message(self.user_name, message)

                time.sleep(1)

                if self.is_vision_enabled:
                    func.run_server_llava()
                    self.wait_for_log_message('llava')

                img = QImageReader(self.image_path)
                img.setAutoTransform(True)
                scale = 300 / img.size().width()
                height = int(img.size().height() * scale)
                img.setScaledSize(QSize(300, height))
                img = img.read()

                buffer = QByteArray()
                qbuffer = QBuffer(buffer)
                qbuffer.open(QBuffer.ReadWrite)
                img.save(qbuffer, "PNG")
                base64_data = base64.b64encode(buffer.data()).decode()

                image_html = f'<img src="data:image/png;base64,{base64_data}" style="max-height: 300px;"><br><br>'
                self.chat_display.append(image_html)

                # TODO: test
                cap = llava_service.get_caption(self.image_path)
                func.kill_server_llava()
                message = message + f' !(image)[alt text={cap.strip()}]'

                custom_stop_sequence = [self.user_name + ':', self.user_name + ': ', '!(image)', '!(gif)', '!(png)']

                if not self.if_first:
                    self.prompt = self.sys_prompt + message + '\n' + self.ai_name + ':'
                    print('1:' + self.prompt)
                    response_content = func.get_response(self.prompt, custom_stop_sequence,
                                                         self.n_pridict_spinbox.value(),
                                                         self.temperature_spinbox.value())
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
                                                         self.n_pridict_spinbox.value(),
                                                         self.temperature_spinbox.value())
                    self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
                    if response_content.endswith("\n"):
                        self.next_prompt = self.next_prompt + response_content + self.user_name + ":"
                    else:
                        self.next_prompt = self.next_prompt + response_content + "\n" + self.user_name + ":"
            else:
                self.setWindowTitle("Matcha Chat (Generating, plz wait....)")
                self.append_message(self.user_name, message)

                custom_stop_sequence = [self.user_name + ':', self.user_name + ': ', '!(image)', '!(gif)', '!(png)']

                if not self.if_first:
                    self.prompt = self.sys_prompt + message + '\n' + self.ai_name + ':'
                    print('1:' + self.prompt)
                    response_content = func.get_response(self.prompt, custom_stop_sequence, self.n_pridict_spinbox.value(),
                                                         self.temperature_spinbox.value())
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
                                                         self.n_pridict_spinbox.value(), self.temperature_spinbox.value())
                    self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
                    if response_content.endswith("\n"):
                        self.next_prompt = self.next_prompt + response_content + self.user_name + ":"
                    else:
                        self.next_prompt = self.next_prompt + response_content + "\n" + self.user_name + ":"

            self.input_line.clear()
            self.is_to_send_image = False
            self.image_path = ""
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
    os.system('taskkill /f /im llava-v1.5-7b-q4-server.llamafile.exe')


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('./icon.png'))
    app.setStyle('Fusion')

    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(28, 28, 28))
    dark_palette.setColor(QPalette.AlternateBase, QColor(32, 32, 32))

    dark_palette.setColor(QPalette.ToolTipBase, Qt.black)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(37, 37, 37))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150))

    app.setPalette(dark_palette)

    app.aboutToQuit.connect(on_close)
    chat_ui = ChatUI()
    chat_ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
