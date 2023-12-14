import configparser
import os
import re

import requests
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QVBoxLayout,
                               QPushButton, QProgressBar, QDialog, QLabel, QMessageBox, QLineEdit, QComboBox)


class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal()
    error = Signal(str)

    def __init__(self, url, dest):
        super().__init__()
        self.url = url
        self.dest = dest
        self.is_canceled = False

    def cancel_download(self):
        self.is_canceled = True

    def run(self):
        try:
            headers = {}
            if os.path.exists(self.dest):
                headers['Range'] = f'bytes={os.path.getsize(self.dest)}-'

            with requests.get(self.url, stream=True, headers=headers, timeout=10) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                if 'content-range' in r.headers:
                    total_size = int(r.headers.get('content-range').split('/')[1])

                with open(self.dest, 'ab') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if self.is_canceled:
                            self.finished.emit()
                            return
                        if chunk:
                            f.write(chunk)
                            self.progress.emit(int(os.path.getsize(self.dest) / total_size * 100))
            self.progress.emit(100)

        except requests.RequestException as e:
            self.error.emit(f"Download error: {e}")
        finally:
            self.finished.emit()


class DownloadDialog(QDialog):
    def __init__(self, url, dest, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest = dest
        self.model_urls = {
            "Wizard Vicuna 7B Uncensored Q5, 4.7GB": "https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGUF/resolve/main/Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf?download=true",
            "Stablelm Zephyr 3B Q5 1.99GB": "https://huggingface.co/TheBloke/stablelm-zephyr-3b-GGUF/resolve/main/stablelm-zephyr-3b.Q5_K_M.gguf?download=true",
            "TinyLlama Chat 1.1B Q4 0.6GB": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v0.3-GGUF/resolve/main/tinyllama-1.1b-chat-v0.3.Q4_K_M.gguf?download=true",
        }
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Download Manager")
        self.setGeometry(300, 300, 300, 150)
        layout = QVBoxLayout()

        self.model_selector = QComboBox(self)
        self.populate_models()
        layout.addWidget(self.model_selector)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.download_button = QPushButton('Start Download', self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.cancel_button = QPushButton('Cancel Download', self)
        self.cancel_button.clicked.connect(self.cancel_download)
        layout.addWidget(self.cancel_button)

        self.set_url_button = QPushButton('...', self)
        self.set_url_button.clicked.connect(self.set_download_url)
        layout.addWidget(self.set_url_button)

        self.setLayout(layout)

    @staticmethod
    def save_model_filename(filename):
        config = configparser.ConfigParser()
        config_file = './config.ini'

        if not os.path.exists(config_file):
            open(config_file, 'w').close()

        config.read(config_file)
        if 'Download' not in config.sections():
            config.add_section('Download')

        if 'Model' not in config.sections():
            config.add_section('Model')

        config.set('Download', 'model_filename', filename)

        config.set('Model', 'is_small', 'No' if filename == "Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf" else 'Yes')

        with open(config_file, 'w') as configfile:
            config.write(configfile)

    def populate_models(self):
        for model_name in self.model_urls.keys():
            self.model_selector.addItem(model_name)
        self.model_selector.currentIndexChanged.connect(self.on_model_change)

    def on_model_change(self):
        model_name = self.model_selector.currentText()
        self.url = self.model_urls[model_name]

    def set_download_url(self):

        self.url_input_dialog = URLInputDialog(self)
        if self.url_input_dialog.exec():
            self.url = self.url_input_dialog.get_url()

    @staticmethod
    def extract_filename_from_url(url):
        match = re.search(r'/([^/?]+)(\?|$)', url)
        return match.group(1) if match else None

    def start_download(self):
        filename = self.extract_filename_from_url(self.url)
        if filename:
            self.dest = os.path.join(os.path.dirname(self.dest), filename)
        self.download_thread = DownloadThread(self.url, self.dest)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.show_error_message)
        self.download_thread.start()
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

    def cancel_download(self):

        self.download_thread.cancel_download()
        self.cancel_button.setEnabled(False)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Download Error", message)
        self.download_button.setEnabled(True)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def download_finished(self):
        filename = self.extract_filename_from_url(self.url)
        if filename:
            self.save_model_filename(filename)
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        print("Download finished!")


class URLInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Customized Model")
        self.setGeometry(400, 400, 200, 100)
        layout = QVBoxLayout()

        self.url_label = QLabel("Enter URL to the model file:", self)
        layout.addWidget(self.url_label)

        self.url_text = QLineEdit(self)
        layout.addWidget(self.url_text)

        self.set_button = QPushButton('Set', self)
        self.set_button.clicked.connect(self.accept)
        layout.addWidget(self.set_button)

        self.setLayout(layout)

    def get_url(self):
        return self.url_text.text()
