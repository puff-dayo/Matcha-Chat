import base64
import json
import os
import sys
import time

import psutil
from PySide6.QtCore import QDateTime, QObject, Signal, Qt, QSize, QByteArray, QBuffer, QThread
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QIcon, QPalette, QImage, QImageReader
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                               QTextEdit, QLineEdit, QPushButton, QGroupBox,
                               QFormLayout, QSpinBox, QLabel, QFileDialog, QMessageBox, QDoubleSpinBox, QFrame)

import cap_dl
import cuda_dl
import func
import llama_dl
import llava_service
import model_dl


class ParameterController(QObject):
    thread_count_changed = Signal(int)
    cache_size_changed = Signal(int)
    n_predict_change = Signal(int)


parameter_controller = ParameterController()

card_dir = os.path.join(os.getcwd(), 'character_cards')
os.makedirs(card_dir, exist_ok=True)


class MemoryMonitorThread(QThread):
    update_signal = Signal(str)

    def run(self):
        while True:
            total_memory = 0
            for process in psutil.process_iter(attrs=['name', 'memory_info']):
                process_info = process.as_dict(attrs=['name', 'memory_info'])
                if process_info['name'] in ['llava-v1.5-7b-q4-server.llamafile.exe', 'server.exe', 'matcha_gui.exe']:
                    total_memory += process_info['memory_info'].rss
            available_memory_gb = psutil.virtual_memory().available / (1024 * 1024 * 1024)
            memory_usage_str = f"Memory: Using {total_memory / (1024 * 1024 * 1024):.2f}GB, Available {available_memory_gb:.2f}GB "
            self.update_signal.emit(memory_usage_str)
            self.sleep(1)


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

        self.is_first = False
        self.left_size = ""
        temp_dir = os.path.join(os.getcwd(), 'temp')
        for filename in os.listdir(temp_dir):
            if filename.endswith(".log"):
                file_path = os.path.join(temp_dir, filename)
                os.remove(file_path)

        self.init_width = 800
        self.init_height = 600
        self.resize(self.init_width, self.init_height)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.sys_prompt = ("Fluffy, the cute 16 years old maid, exudes irresistible charm with her wagging"
                           " tail, perky cat ears, and revealing outfit. She likes talking with her mistress about "
                           "everything. She showers her mistress with affection through gentle rubs, "
                           "purrs of contentment, and erotic pleasure. She brings joy and companionship, "
                           "forever cherished by her adoring mistress.\nPairs of parentheses are used to indicate "
                           "actions.\nHere is a transcript of a never ending text dialog, where Mistress interacts "
                           "with her girl Fluffy.\nFluffy:Welcome home, my mistress. (lifts her "
                           "mini-skirt)\nMistress:")
        self.prompt = ""
        self.next_prompt = ""
        self.previous_state = None
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
        self.width_rem = self.width()
        self.initThread()

    def initThread(self):
        self.thread = MemoryMonitorThread()
        self.thread.update_signal.connect(self.updateMemoryUsage)
        self.thread.start()

    def updateMemoryUsage(self, memory_usage_str):
        self.ram_label.setText(memory_usage_str)

    def init_ui(self):
        hbox = QHBoxLayout(self)

        self.left_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.left_layout.addWidget(self.chat_display)

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
        self.chat_display.setStyleSheet("border: none; background-color: transparent;")

        tool_bar.addWidget(self.photo_button)
        tool_bar.addWidget(download_button)
        tool_bar.addWidget(undo_button)
        tool_bar.addWidget(delete_button)
        tool_bar.addWidget(settings_button)
        tool_bar.addStretch()
        self.ram_label = QLabel("Memory Usage", self)
        tool_bar.addWidget(self.ram_label)

        self.left_layout.addLayout(tool_bar)

        self.input_line = CustomTextEdit()
        self.input_line.setMinimumHeight(50)
        self.input_line.setMaximumHeight(100)
        self.input_line.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left_layout.addWidget(self.input_line)

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

        self.left_layout.addLayout(button_layout)

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
        self.button4 = QPushButton("Use GPU (SLOW!)")
        self.button4.clicked.connect(self.check_gpu)
        group_layout.addRow(self.button4)
        self.buttonC = QPushButton("Enable vision ability")
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

        hbox.addLayout(self.left_layout, 5)
        hbox.addWidget(self.right_frame, 2)

        self.setWindowTitle("Matcha Chat")
        self.setGeometry(150, 150, 800, 600)
        self.checkFile()

    def on_ctrl_enter_pressed(self):
        self.send_message()

    def check_gpu(self):
        if self.detect_file('./pkgs', 'server.exe'):
            if not self.detect_file('./pkgs', 'openblas.dll'):
                self.button4.setText('Using GPU[√]')
                self.checkFile()
            else:
                for filename in os.listdir('./pkgs'):
                    if os.path.isfile(os.path.join('./pkgs', filename)):
                        os.remove(os.path.join('./pkgs', filename))
                self.cuda_llamacpp_dler()
                self.button4.setText('Using GPU[√]')
                self.checkFile()
            self.checkFile()
        else:
            self.cuda_llamacpp_dler()
            self.button4.setText('Using GPU[√]')
            self.checkFile()

    def cap_dler(self):
        cap_dl.DownloadDialog().exec()

    def check_vision(self):
        if not self.detect_file('./models/cap', 'pytorch_model.bin'):
            self.buttonC.setText("Enable vision ability")
            self.cap_dler()
            self.checkFile()
        else:
            self.buttonC.setText('Enabled vision ability[√]')
            self.is_vision_enabled = True
            self.checkFile()

    def on_photo_clicked(self):
        if self.image_path != "":
            self.is_to_send_image = False
            self.image_path = ""
            self.photo_button.setIcon(QIcon('./icons/photo.png'))
            return
        file_name, _ = QFileDialog.getOpenFileName(self, "Select an image", "", "Image (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.is_to_send_image = True
            self.image_path = file_name
            image = QImage(file_name)
            self.photo_button.setIcon(QIcon('./icons/photo_hover.png'))
            if image.isNull():
                self.photo_button.setIcon(QIcon('./icons/photo.png'))
                return

    def save_text_to_html(self):
        file_name, _ = QFileDialog.getSaveFileName(
            None, "Save File", "", "HTML Files (*.html;*.htm)"
        )
        if file_name:
            html_content = self.chat_display.toHtml()
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(html_content)

    def on_download_clicked(self):
        self.save_text_to_html()

    def on_undo_clicked(self):
        if self.previous_state:
            self.chat_display.setHtml(self.previous_state["chat_history"])
            self.next_prompt = self.previous_state["next_prompt"]
            self.input_line.setText(self.previous_state["input_message"])
            self.if_first = self.previous_state["is_first"]
            self.is_to_send_image = self.previous_state["is_image"]
            self.image_path = self.previous_state["image_path"]

    def toggle_settings(self):
        is_visible = self.right_frame.isVisible()
        self.right_frame.setVisible(not is_visible)

        if self.left_size == "":
            self.left_size = round(800 / 7 * 5)

        if is_visible:
            self.setMinimumSize(300, 200)
            self.resize(self.left_size, self.height())
        else:
            self.resize(self.width_rem, self.height())

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
        for filename in os.listdir('./pkgs'):
            if os.path.isfile(os.path.join('./pkgs', filename)):
                os.remove(filename)
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
                self.button4.setText('Using GPU[√]')
        if self.detect_file('./models', 'llava-v1.5-7b-q4-server.llamafile.exe'):
            self.buttonC.setText('Enabled vision ability[√]')
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
            self.display_image()
        else:
            cursor.insertText(f"{message}\n\n", text_format)

        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        self.chat_display.ensureCursorVisible()

    def save_current_state(self):
        self.previous_state = {
            "chat_history": self.chat_display.toHtml(),
            "next_prompt": self.next_prompt,
            "input_message": self.input_line.toPlainText(),
            "is_first": self.if_first,
            "is_image": self.is_to_send_image,
            "image_path": self.image_path,
        }

    def display_image(self):
        img = QImageReader(self.image_path)
        img.setAutoTransform(True)

        screen = QApplication.screens()[0]
        dpi_scale = screen.logicalDotsPerInch() / 96

        target_height = 300 * dpi_scale
        scale = target_height / img.size().height()
        width = int(img.size().width() * scale)
        img.setScaledSize(QSize(width, target_height))

        img = img.read()

        buffer = QByteArray()
        qbuffer = QBuffer(buffer)
        qbuffer.open(QBuffer.ReadWrite)
        img.save(qbuffer, "PNG", 90)
        base64_data = base64.b64encode(buffer.data()).decode()

        image_html = f'<img src="data:image/png;base64,{base64_data}"><br><br>'
        self.chat_display.append(image_html)

    # def send_message(self):
    #     self.save_current_state()
    #     message = self.input_line.toPlainText()
    #     custom_stop_sequence = [self.user_name + ':', self.user_name + ': ', '!(image)', '!(gif)', '!(png)']
    #     self.setWindowTitle("Matcha Chat (Generating, plz wait....)")
    #     self.append_message(self.user_name, message)
    #
    #     if message:
    #         if self.is_to_send_image:
    #
    #             func.kill_server()
    #             time.sleep(1)
    #
    #             if self.is_vision_enabled:
    #                 func.run_server_llava()
    #                 self.wait_for_log_message('llava')
    #
    #             self.display_image()
    #
    #             cap = llava_service.get_caption(self.image_path)
    #             func.kill_server_llava()
    #
    #             func.run_server(self.thread_count_spinbox.value(), self.content_size_spinbox.value(),
    #                             self.gpu_layer_spinbox.value())
    #             self.wait_for_log_message('llama')
    #             message = message + f' !(image)[alt text={cap.strip()}]'
    #
    #
    #             if not self.if_first:
    #                 self.prompt = self.sys_prompt + message + '\n' + self.ai_name + ':'
    #                 print('1:' + self.prompt)
    #                 response_content = func.get_response(self.prompt, custom_stop_sequence,
    #                                                      self.n_pridict_spinbox.value(),
    #                                                      self.temperature_spinbox.value())
    #                 self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
    #                 self.if_first = True
    #                 if response_content.endswith("\n"):
    #                     self.next_prompt = self.prompt + response_content + self.user_name + ":"
    #                 else:
    #                     self.next_prompt = self.prompt + response_content + "\n" + self.user_name + ":"
    #             else:
    #                 self.next_prompt = self.next_prompt + message + '\n' + self.ai_name + ':'
    #                 print('2:' + self.next_prompt)
    #                 response_content = func.get_response(self.next_prompt, custom_stop_sequence,
    #                                                      self.n_pridict_spinbox.value(),
    #                                                      self.temperature_spinbox.value())
    #                 self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
    #                 if response_content.endswith("\n"):
    #                     self.next_prompt = self.next_prompt + response_content + self.user_name + ":"
    #                 else:
    #                     self.next_prompt = self.next_prompt + response_content + "\n" + self.user_name + ":"
    #         else:
    #             if not self.if_first:
    #                 self.prompt = self.sys_prompt + message + '\n' + self.ai_name + ':'
    #                 print('1:' + self.prompt)
    #                 response_content = func.get_response(self.prompt, custom_stop_sequence, self.n_pridict_spinbox.value(),
    #                                                      self.temperature_spinbox.value())
    #                 self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
    #                 self.if_first = True
    #                 if response_content.endswith("\n"):
    #                     self.next_prompt = self.prompt + response_content + self.user_name + ":"
    #                 else:
    #                     self.next_prompt = self.prompt + response_content + "\n" + self.user_name + ":"
    #             else:
    #                 self.next_prompt = self.next_prompt + message + '\n' + self.ai_name + ':'
    #                 print('2:' + self.next_prompt)
    #                 response_content = func.get_response(self.next_prompt, custom_stop_sequence,
    #                                                      self.n_pridict_spinbox.value(), self.temperature_spinbox.value())
    #                 self.append_message(self.ai_name, response_content.lstrip().rstrip('\n'))
    #                 if response_content.endswith("\n"):
    #                     self.next_prompt = self.next_prompt + response_content + self.user_name + ":"
    #                 else:
    #                     self.next_prompt = self.next_prompt + response_content + "\n" + self.user_name + ":"
    #
    #         self.input_line.clear()
    #         self.photo_button.setIcon(QIcon('./icons/photo.png'))
    #         self.is_to_send_image = False
    #         self.image_path = ""
    #         self.setWindowTitle("Matcha Chat")

    def start_work_thread(self, message, custom_stop_sequence):
        self.work_thread = WorkThread(message, custom_stop_sequence, self.is_to_send_image, self.is_first,
                                      self.is_vision_enabled, self.image_path, self.thread_count_spinbox.value(),
                                      self.gpu_layer_spinbox.value(), self.content_size_spinbox.value(),
                                      self.n_pridict_spinbox.value(), self.temperature_spinbox.value(),
                                      self.sys_prompt, self.ai_name, self.next_prompt)
        self.work_thread.finished.connect(self.on_work_finished)
        self.work_thread.start()

    def on_work_finished(self, processed_message, is_first, next_prompt):
        print('Worker finished!')
        self.reset_message_state()
        self.append_message(self.ai_name, processed_message.strip())
        self.next_prompt = next_prompt
        self.update_next_prompt(processed_message)
        self.is_first = is_first

    def send_message(self):
        if self.input_line.toPlainText() == "":
            return
        if self.button3.isEnabled():
            return
        self.save_current_state()
        self.setWindowTitle("Matcha Chat (Generating, plz wait....)")
        message = self.input_line.toPlainText()
        custom_stop_sequence = [self.user_name + ':', self.user_name + ': ', '!(image)', '!(gif)', '!(png)']
        self.append_message(self.user_name, message)
        self.input_line.clear()
        self.start_work_thread(message, custom_stop_sequence)

    def update_next_prompt(self, response_content):
        line_ending = "\n" if not response_content.endswith("\n") else ""
        self.next_prompt += response_content + line_ending + self.user_name + ":"

    def reset_message_state(self):
        self.photo_button.setIcon(QIcon('./icons/photo.png'))
        self.is_to_send_image = False
        self.image_path = ""
        self.setWindowTitle("Matcha Chat")

    #########################################################################################

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


class WorkThread(QThread):
    finished = Signal(str, bool, str)

    def __init__(self, message, custom_stop_sequence, is_to_send_image, if_first, is_vision_enabled, image_path,
                 thread, gpu, content, predict, temp, sys_pr, ai_name, next_pr, parent=None):
        super().__init__(parent)
        self.current_prompt = None
        self.next_prompt = next_pr
        self.gpu = gpu
        self.content = content
        self.is_to_send_image = is_to_send_image
        self.message = message
        self.custom_stop_sequence = custom_stop_sequence
        self.if_first = if_first
        self.is_vision_enabled = is_vision_enabled
        self.image_path = image_path
        self.thread = thread
        self.predict = predict
        self.temp = temp
        self.sys_prompt = sys_pr
        self.ai_name = ai_name

    def check_log_file(self, file):
        if not os.path.exists(os.path.join(os.getcwd(), 'temp') + f"/{file}_output.log"):
            print("log not exist")
            return False
        with open(f"./temp/{file}_output.log", "r") as file:
            logs = file.read()
            # print("loaded log")
            return "all slots are idle and system prompt is empty, clear the KV cache" in logs

    def wait_for_log_message(self, file):
        print("start waiting log")
        while not self.check_log_file(file):
            pass

    def handle_image_processing(self, message):
        func.kill_server()
        time.sleep(1)

        if self.is_vision_enabled:
            func.run_server_llava()
            self.wait_for_log_message('llava')

        cap = llava_service.get_caption(self.image_path)
        func.kill_server_llava()

        print(f"to start server with {self.thread},{self.content},{self.gpu}")
        func.run_server(self.thread,
                        self.content,
                        self.gpu)
        print("start server")
        self.wait_for_log_message('llama')
        message += f' !(image)[alt text={cap.strip()}]'
        return message

    def update_prompt_and_send_message(self, message, custom_stop_sequence):
        self.current_prompt = self.construct_prompt(message)
        print('Prompt:', self.current_prompt)
        response_content = func.get_response(self.current_prompt, custom_stop_sequence,
                                             self.predict, self.temp)
        return response_content

    def construct_prompt(self, message):
        if not self.if_first:
            self.if_first = True
            return self.sys_prompt + message + '\n' + self.ai_name + ':'
        return self.next_prompt + message + '\n' + self.ai_name + ':'

    def run(self):
        if self.is_to_send_image:
            print("Image start processing.")
            self.message = self.handle_image_processing(self.message)
            print("Image:" + self.message)
        processed_message = self.update_prompt_and_send_message(self.message, self.custom_stop_sequence)
        self.finished.emit(processed_message, self.if_first, self.current_prompt)


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
