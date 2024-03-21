import json
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QVBoxLayout, QListWidget, QPushButton, QMessageBox, QMainWindow, QWidget, QLabel, \
    QGridLayout, QHBoxLayout

import services.windows_api_handler
from components.custom_titlebar import CustomTitleBar
from services.file_downloader import DownloaderDialog
from services.files_downloader import DownloaderDialog as MultiDownloaderDiag

temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)
print(temp_dir)

models_dir = os.path.join(os.getcwd(), 'models')
os.makedirs(models_dir, exist_ok=True)
print(models_dir)

backend_dir = os.path.join(os.getcwd(), 'backend')
os.makedirs(backend_dir, exist_ok=True)

translator_models_dir = os.path.join(models_dir, 'translator')
os.makedirs(translator_models_dir, exist_ok=True)
print(translator_models_dir)


class DownloaderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        _base_dir = os.path.dirname(__file__)
        _json_file = os.path.join(_base_dir, "models", "model_list.json")

        self.jsonfile = _json_file
        self.resize(1024, 512)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowMaximizeButtonHint)
        self.titleBar = CustomTitleBar(self, custom_title="Matcha Chat 2 - Downloader")
        self.setMenuWidget(self.titleBar)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        self.setStyleSheet("background:transparent")
        self.windowEffect = services.windows_api_handler.WindowEffect()
        self.windowEffect.setAcrylicEffect(int(self.winId()), gradientColor='00101080')

        central_widget = QWidget(self)
        gridLayout = QGridLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        gridLayout.addLayout(self.left_layout, 0, 0)
        gridLayout.addLayout(self.right_layout, 0, 1)

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

        # Left layout
        gridLayout.setContentsMargins(10, 10, 10, 10)
        gridLayout.setSpacing(10)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.file_list_widget.setStyleSheet("""
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

        self.left_layout.addWidget(QLabel("1. Download a llama.cpp backend"))
        download_backend = QPushButton("Download")
        download_backend.setStyleSheet(button_style)
        left_hox_1 = QHBoxLayout()
        left_hox_1.addWidget(QLabel(" llama.cpp b2487 + clblast, 4.4 MB"))
        left_hox_1.addWidget(download_backend)
        download_backend.clicked.connect(self.download_backend)
        self.left_layout.addLayout(left_hox_1)

        self.left_layout.addWidget(QLabel("2. Download a LLM model"))
        self.left_layout.addWidget(self.file_list_widget)
        self.download_button = QPushButton("Download Selected")
        self.download_button.setStyleSheet(button_style)
        self.custom_download_button = QPushButton("Download Custom...")
        self.custom_download_button.setStyleSheet(button_style)
        self.left_layout.addWidget(self.download_button)
        self.left_layout.addWidget(self.custom_download_button)
        self.download_button.clicked.connect(self.download_model)
        self.custom_download_button.clicked.connect(self.custom_download)

        self.right_layout.addWidget(QLabel("3. Download a translator model (optional)"))
        download_translator = QPushButton("Download")
        download_translator.setStyleSheet(button_style)
        download_translator.clicked.connect(self.download_translator)
        right_hox_1 = QHBoxLayout()
        right_hox_1.addWidget(QLabel(" m2m-100 1.2b(int8), 1.3 GB"))
        right_hox_1.addWidget(download_translator)
        self.right_layout.addLayout(right_hox_1)

        self.right_layout.addStretch()

        self.left_layout.setContentsMargins(8, 8, 8, 8)
        self.left_layout.setSpacing(8)

        self.right_layout.setContentsMargins(8, 8, 8, 8)
        self.right_layout.setSpacing(8)

        self.setCentralWidget(central_widget)
        self.setWindowTitle("Matcha Chat 2")
        self.load_files_from_json(_json_file)

    def download_translator(self):
        file_urls = [
            'https://huggingface.co/JustFrederik/m2m_100_1.2b_ct2_int8/resolve/main/config.json?download=true',
            'https://huggingface.co/JustFrederik/m2m_100_1.2b_ct2_int8/resolve/main/model.bin?download=true',
            'https://huggingface.co/JustFrederik/m2m_100_1.2b_ct2_int8/resolve/main/shared_vocabulary.txt?download=true',
            'https://huggingface.co/JustFrederik/m2m_100_1.2b_ct2_int8/resolve/main/spm.128k.model?download=true'
        ]
        self.download_trans_diag = MultiDownloaderDiag(destination=translator_models_dir,
                                                       file_info="M2M100 Multilingual Machine Translation:\n4 files in total, 1.3 GB",
                                                       parent=self, urls=file_urls)
        self.download_trans_diag.show()

    def download_backend(self):
        self.download_backend_diag = DownloaderDialog(destination=backend_dir,
                                                      url="https://github.com/ggerganov/llama.cpp/releases/download/b2487/llama"
                                                          "-b2487-bin-win-clblast-x64.zip",
                                                      file_info="Pre-built llama.cpp binaries:\nb2487-clblast-x64, 4.4 MB",
                                                      parent=self, unzip=True)
        self.download_backend_diag.show()

    def load_files_from_json(self, _json_file):
        try:
            with open(_json_file, 'r') as j_file:
                files = json.load(j_file)
                for file in files:
                    self.file_list_widget.addItem(file['name'])
        except Exception as e:
            QMessageBox.critical(self, "Error:", f"JSON read failed: {e}")

    def download_model(self):
        selected_items = self.file_list_widget.selectedItems()
        if selected_items:
            file_name = selected_items[0].text()
            try:
                with open(self.jsonfile, 'r') as j_file:
                    files = json.load(j_file)
                    url = None
                    for file in files:
                        if file['name'] == file_name:
                            url = file['url']
                            break
                    if url:
                        print(url)
                        self.dialog = DownloaderDialog(destination=models_dir, url=url, file_info=file_name,
                                                       parent=self)
                        self.dialog.show()
                    else:
                        print("File url not found.")
            except Exception as e:
                print(f"Error reading file: {e}")
        else:
            pass

    def custom_download(self):
        QMessageBox.information(self, "UwU", "Popup")
