import json
import os
from configparser import ConfigParser

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPalette, QColor, QCursor, QDesktopServices
from PySide6.QtWidgets import (QVBoxLayout,
                               QMainWindow,
                               QWidget, QGridLayout, QLabel, QComboBox, QHBoxLayout, QLineEdit, QTextEdit, QPushButton,
                               QFileDialog, QMessageBox, QCheckBox)

import services.settings_handler as Settings
import services.windows_api_handler
from components.custom_sliders import CustomSlider, CustomSliderDouble
from components.custom_titlebar import CustomTitleBar


# TODO: construct config path and replace all hard encoded strings below


class SettingsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(800, 768)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowMaximizeButtonHint)
        self.titleBar = CustomTitleBar(self, custom_title="Matcha Chat 2 - Settings")
        self.setMenuWidget(self.titleBar)
        self.setWindowTitle("Matcha Chat 2")

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        self.setStyleSheet("background:transparent")
        self.windowEffect = services.windows_api_handler.WindowEffect()
        self.windowEffect.setAcrylicEffect(int(self.winId()), gradientColor='00101080')

        central_widget = QWidget(self)
        gridLayout = QGridLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Main layout
        gridLayout.setContentsMargins(10, 10, 10, 10)
        gridLayout.setSpacing(10)

        # 1. Model Config
        model_config = QVBoxLayout()
        model_config.setContentsMargins(10, 10, 10, 10)
        model_config.setSpacing(10)

        left_title_layout = QHBoxLayout()
        left_title_layout.setAlignment(Qt.AlignVCenter)
        left_title = QLabel("> LLM model config <")
        left_title.setAlignment(Qt.AlignVCenter)
        left_title_layout.addStretch()
        left_title_layout.addWidget(left_title)
        left_title_layout.addStretch()

        model_config.addLayout(left_title_layout)

        # 1.1
        self.model_select_box = QComboBox()
        combo_style = """
        QComboBox {
                border: 0px solid;
                border-radius: 0px;
                background-color: #599e5e;
                color: white;
                padding: 0px;
        }
        
        QComboBox::drop-down {
            background-color: #e9ae21;
        }
        
        QComboBox QAbstractItemView {
            border: 0px solid;
            background-color: #599e5e;
            color: white;
            selection-background-color: #599e5e;
            selection-color: white;
        }
        """
        self.model_select_box.setStyleSheet(combo_style)

        self.loadSelection()
        self.loadFiles()
        if self.selected_file is not None:
            if self.selected_file != "":
                index = self.model_select_box.findText(self.selected_file)
                if index >= 0:
                    self.model_select_box.setCurrentIndex(index)
        else:
            self.selected_file = ""
        self.model_select_box.currentIndexChanged.connect(self.fileSelected)
        model_config.addWidget(QLabel("# Model select: "))
        model_config.addWidget(self.model_select_box)
        model_config.addWidget(QLabel("\n# Model parameters: "))
        # 1.2
        self.thread_slider = CustomSlider("Threads: ", 14, 1, 16, 128,
                                          "Set the number of threads for processing.\n\nRange: 1-128.", 1)
        model_config.addWidget(self.thread_slider)
        # 1.3
        self.content_size_slider = CustomSlider("Capacity: ", 4096, 256, 4096, 65536,
                                                "The maximum sequence length that this model might ever be used "
                                                "with.\n\nRange: 256-65536.", 1)
        model_config.addWidget(self.content_size_slider)
        # 1.4
        self.temperature_slider = CustomSliderDouble("Temp: ", 0.7, 0.0, 2.0,
                                                     "Higher values like 0.8 will make the output more random,\nwhile lower values like 0.2 will make it more focused and deterministic.\n\nRange: 0.0-2.0.",
                                                     1)
        model_config.addWidget(self.temperature_slider)
        # 1.5
        self.predict_size_slider = CustomSlider("NewPredict:", 512, -1, 384, 8192,
                                                "Set the maximum number of tokens to predict when generating text.\n\n(-1 = infinity)",
                                                1)
        model_config.addWidget(self.predict_size_slider)
        # 1.6
        self.gpu_layers_slider = CustomSlider("GPULayers:", 0, 0, 16, 64,
                                              "This option allows offloading some layers to the GPU for computation.\nGenerally results in decreased performance.\n\nNeeds much more RAM.\n\nSet to 0 for a weak GPU be faster.",
                                              1)
        model_config.addWidget(self.gpu_layers_slider)
        # 1.A
        model_config.addWidget(QLabel("\n# LongLM parameters: "))
        grp_tip = r"""Set GroupSize to 1 = disable
        
With Llama-2 as the base model, 2~64 are reasonable for group_size;
512~1536 are feasible for neighbor_window. But larger group_size and
smaller neighbor_window are also good in many cases.

T: original capacity
C: the capacity you want

G: group size
N: neighbor window

The rule is: G * T >= C.

I think the authors generally used 512 for N,
but maybe you can go up to T/2.

Remember to change the "capacity" slide as well!

https://arxiv.org/pdf/2401.01325.pdf
"""
        self.grp_n_slider = CustomSlider("GroupSize:", 1, 1, 4, 64,
                                         grp_tip, 1)
        model_config.addWidget(self.grp_n_slider)
        self.grp_w_slider = CustomSlider("Window:", 512, 256, 1536, 4096,
                                         grp_tip, 1)
        model_config.addWidget(self.grp_w_slider)

        help_layout = QHBoxLayout()
        self.help_label = QLabel("More about LongLM", self)
        self.help_label.move(50, 50)
        self.help_label.setStyleSheet("QLabel { color: white; text-decoration: underline; }")
        self.help_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.help_label.mousePressEvent = self.open_help_page
        help_layout.addStretch()
        help_layout.addWidget(self.help_label)
        model_config.addLayout(help_layout)

        # 1.X translator config
        left_middle_title_layout = QHBoxLayout()
        left_middle_title_layout.setAlignment(Qt.AlignVCenter)
        left_middle_title = QLabel("\n> Translator config <")
        left_middle_title.setAlignment(Qt.AlignVCenter)
        left_middle_title_layout.addStretch()
        left_middle_title_layout.addWidget(left_middle_title)
        left_middle_title_layout.addStretch()

        model_config.addLayout(left_middle_title_layout)

        # 1.x1
        hbox_on = QHBoxLayout()

        checked_style = """
        QCheckBox {
                spacing: 5px;
            }

            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 2px solid white;
                border-radius: 0px;
            }

            QCheckBox::indicator:checked {
                background-color: #69ae6e;
                border: 2px solid white;
                image: url('transparent_checkmark.png');
            }
        """

        self.output_switch = QCheckBox("Output translator")
        self.output_switch.setStyleSheet(checked_style)
        self.output_switch.setCheckable(True)
        self.output_switch.setChecked(False)
        self.output_switch.stateChanged.connect(self.switch_state_changed)
        hbox_on.addWidget(self.output_switch)

        self.input_switch = QCheckBox("Input translator")
        self.input_switch.setStyleSheet(checked_style)
        self.input_switch.setCheckable(True)
        self.input_switch.setChecked(False)
        self.input_switch.stateChanged.connect(self.switch_state_changed)
        hbox_on.addWidget(self.input_switch)

        model_config.addLayout(hbox_on)

        self.language_code_combobox = QComboBox()
        self.language_code_combobox.setStyleSheet(combo_style)
        self.language_code_combobox.setMinimumWidth(50)
        self.language_code_combobox.setEditable(True)
        self.language_code_combobox.addItem("ja")
        self.language_code_combobox.addItem("fr")
        self.language_code_combobox.addItem("de")
        self.language_code_combobox.addItem("es")
        self.language_code_combobox.addItem("zh")
        self.language_code_combobox.addItem("vi")
        self.language_code_combobox.currentTextChanged.connect(self.switch_state_changed)

        hbox_lang = QHBoxLayout()
        hbox_lang.addStretch()
        hbox_lang.addWidget(QLabel("Target language: "))
        hbox_lang.addWidget(self.language_code_combobox)

        model_config.addLayout(hbox_lang)

        model_config.addStretch()

        # 2. Prompt
        model_prompt = QVBoxLayout()
        model_prompt.setContentsMargins(10, 10, 10, 10)
        model_prompt.setSpacing(10)

        right_title_layout = QHBoxLayout()
        right_title_layout.setAlignment(Qt.AlignVCenter)
        right_title = QLabel("> Prompt and role config <")
        right_title.setAlignment(Qt.AlignVCenter)
        right_title_layout.addStretch()
        right_title_layout.addWidget(right_title)
        right_title_layout.addStretch()

        model_prompt.addLayout(right_title_layout)

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

        self.sender_name_line_edit = QLineEdit()
        self.sender_name_line_edit.setStyleSheet(hey_stylesheet)
        model_prompt.addWidget(QLabel("# User name:"))
        model_prompt.addWidget(self.sender_name_line_edit)

        self.ai_name_line_edit = QLineEdit()
        self.ai_name_line_edit.setStyleSheet(hey_stylesheet)
        model_prompt.addWidget(QLabel("\n# AI name:"))
        model_prompt.addWidget(self.ai_name_line_edit)

        self.system_prompt_text_edit = QTextEdit()
        self.system_prompt_text_edit.setAcceptRichText(False)
        self.system_prompt_text_edit.setStyleSheet(hey_stylesheet)
        model_prompt.addWidget(QLabel("\n# System prompt:"))
        model_prompt.addWidget(self.system_prompt_text_edit)

        for widget in [self.ai_name_line_edit, self.sender_name_line_edit, self.system_prompt_text_edit]:
            palette = widget.palette()
            palette.setColor(QPalette.Highlight, QColor("#5bb481"))
            widget.setPalette(palette)

        # 2.X Character card import/export
        chara_card_buttons_layout = QHBoxLayout()

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

        card_import = QPushButton("Import")
        card_import.setStyleSheet(button_style)
        card_import.clicked.connect(self.load_from_json)
        card_export = QPushButton("Export")
        card_export.setStyleSheet(button_style)
        card_export.clicked.connect(self.save_to_json)

        chara_card_buttons_layout.addWidget(QLabel("# Character card: "))
        chara_card_buttons_layout.addStretch()
        chara_card_buttons_layout.addWidget(card_import)
        chara_card_buttons_layout.addWidget(card_export)

        model_prompt.addLayout(chara_card_buttons_layout)

        gridLayout.addLayout(model_config, 0, 0)
        gridLayout.addLayout(model_prompt, 0, 1)

        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)

        settings = Settings.load_settings()
        self.update_sliders(settings)

        prompt_settings = Settings.load_prompt_settings()
        self.update_text_edits(prompt_settings)

        trans_settings = Settings.load_translator_settings()
        self.update_trans_settings(trans_settings)

    def open_help_page(self, event):
        url = "https://github.com/datamllab/LongLM#4how-to-choose-the-group_size-and-neighbor_window"
        QDesktopServices.openUrl(QUrl(url))

    def switch_state_changed(self):
        settings = {
            'in': '1' if self.input_switch.isChecked() else '0',
            'out': '1' if self.output_switch.isChecked() else '0',
            'target': f'{self.language_code_combobox.currentText()}'
        }
        Settings.save_translator_settings(settings)

    def save_to_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save character card file", "",
                                                   "JSON file (*.json);;All files (*)")
        if file_path:
            data = {
                'ai_name': self.ai_name_line_edit.text(),
                'user_name': self.sender_name_line_edit.text(),
                'sys_prompt': self.system_prompt_text_edit.toPlainText()
            }
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4)
                # QMessageBox.information(self, "Success", "Data saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def load_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load character card file", "",
                                                   "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.ai_name = data.get('ai_name', '')
                    self.user_name = data.get('user_name', '')
                    self.sys_prompt = data.get('sys_prompt', '')

                    self.ai_name_line_edit.setText(self.ai_name)
                    self.sender_name_line_edit.setText(self.user_name)
                    self.system_prompt_text_edit.setText(self.sys_prompt)
                # QMessageBox.information(self, "Success", "Data loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def loadFiles(self):
        path = "./models"
        files = [f for f in os.listdir(path) if f.endswith('gguf')]
        self.model_select_box.addItems(files)

    def fileSelected(self, index):
        selected_file = self.model_select_box.itemText(index)
        self.saveSelection(selected_file)

    def saveSelection(self, selected_file):
        config = ConfigParser()
        config.read('config.ini')
        if not config.has_section('LLM'):
            config.add_section('LLM')
        config.set('LLM', 'selected_file', selected_file)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def loadSelection(self):
        config = ConfigParser()
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            config.add_section('LLM')
            config.set('LLM', 'selected_file', '')
            with open(config_file, 'w') as f:
                config.write(f)
        else:
            config.read(config_file)
            if config.has_option('LLM', 'selected_file'):
                self.selected_file = config.get('LLM', 'selected_file')

    # def load_settings(self):
    #     config = configparser.ConfigParser()
    #
    #     settings = {
    #         'threads': 14,
    #         'capacity': 4096,
    #         'temperature': 0.7,
    #         'new_predict': 512,
    #         'gpu_layers': 0
    #     }
    #
    #     config.read('config.ini')
    #
    #     if config.has_section('Settings'):
    #         for key in settings:
    #             if config.has_option('Settings', key):
    #                 value = config.get('Settings', key)
    #                 if key in ['threads', 'capacity', 'new_predict', 'gpu_layers']:
    #                     settings[key] = int(value)
    #                 elif key == 'temperature':
    #                     settings[key] = float(value)
    #
    #     return settings
    #
    # def load_prompt_settings(self):
    #     config = configparser.ConfigParser()
    #
    #     settings = {
    #         'user_name': "Puff",
    #         'ai_name': "Fluffy",
    #         'sys_prompt': "You are Fluffy, a 16 year old erotic maid, wearing a locked collar, a pair of metal handcuffs, maid costume and a cat ear headband. You are chatting with your mistress, Puff."
    #     }
    #
    #     config.read('config.ini')
    #
    #     if config.has_section('Prompt'):
    #         for key in settings:
    #             if config.has_option('Prompt', key):
    #                 value = config.get('Prompt', key)
    #                 if key in ['user_name', 'ai_name', 'sys_prompt']:
    #                     settings[key] = str(value)
    #
    #     return settings
    #
    # def save_settings(self, settings):
    #     config = configparser.ConfigParser()
    #
    #     config.read('config.ini')
    #     if not config.has_section('Settings'):
    #         config.add_section('Settings')
    #     for key, value in settings.items():
    #         config.set('Settings', key, str(value))
    #
    #     with open('config.ini', 'w') as configfile:
    #         config.write(configfile)
    #
    # def save_prompt_settings(self, settings):
    #     config = configparser.ConfigParser()
    #
    #     config.read('config.ini')
    #     if not config.has_section('Prompt'):
    #         config.add_section('Prompt')
    #     for key, value in settings.items():
    #         config.set('Prompt', key, str(value))
    #
    #     with open('config.ini', 'w') as configfile:
    #         config.write(configfile)

    def update_text_edits(self, settings):
        self.system_prompt_text_edit.setText(settings["sys_prompt"])
        self.ai_name_line_edit.setText(settings["ai_name"])
        self.sender_name_line_edit.setText(settings["user_name"])

    def update_sliders(self, settings):
        self.thread_slider.setValue(settings['threads'])
        self.content_size_slider.setValue(settings['capacity'])
        self.temperature_slider.setValue(settings['temperature'])
        self.predict_size_slider.setValue(settings['new_predict'])
        self.gpu_layers_slider.setValue(settings['gpu_layers'])
        self.grp_n_slider.setValue(settings['grp_n'])
        self.grp_w_slider.setValue(settings['grp_w'])

    def closeEvent(self, event):
        settings = {
            'threads': self.thread_slider.value(),
            'capacity': self.content_size_slider.value(),
            'temperature': self.temperature_slider.value(),
            'new_predict': self.predict_size_slider.value(),
            'gpu_layers': self.gpu_layers_slider.value(),
            'grp_n': self.grp_n_slider.value(),
            'grp_w': self.grp_w_slider.value()
        }

        Settings.save_settings(settings)

        prompt_settings = {
            'user_name': self.sender_name_line_edit.text(),
            'ai_name': self.ai_name_line_edit.text(),
            'sys_prompt': self.system_prompt_text_edit.toPlainText()
        }

        Settings.save_prompt_settings(prompt_settings)

        super().closeEvent(event)

    def update_trans_settings(self, trans_settings):
        self.input_switch.setChecked(trans_settings['in'] == '1')
        self.output_switch.setChecked(trans_settings['out'] == '1')
        self.language_code_combobox.setCurrentText(trans_settings['target'])
