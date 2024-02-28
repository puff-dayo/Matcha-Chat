import os
import shutil
from urllib.parse import urlparse, unquote

import requests
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (QVBoxLayout,
                               QPushButton, QProgressBar, QLabel, QMessageBox, QHBoxLayout, QMainWindow,
                               QWidget)

import services.windows_api_handler
from components.custom_titlebar import CustomTitleBar


class DownloadThread(QThread):
    progress = Signal(int)
    dl_finished = Signal()
    error = Signal(str)

    success = False

    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename
        self.is_canceled = False

    def cancel_download(self):
        self.is_canceled = True

    def run(self):
        temp_directory = os.path.abspath('./temp')
        os.makedirs(temp_directory, exist_ok=True)
        dest = os.path.join(temp_directory, self.filename)

        try:
            headers = {}
            if os.path.exists(dest):
                bytes_downloaded = os.path.getsize(dest)
                headers['Range'] = f'bytes={bytes_downloaded}-'
            else:
                bytes_downloaded = 0

            with requests.get(self.url, stream=True, headers=headers, timeout=10) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                if 'content-range' in r.headers:
                    total_size = int(r.headers.get('content-range').split('/')[1])

                with open(dest, 'ab') as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
                            self.progress.emit(min(int(bytes_downloaded / total_size * 100), 100))

            self.progress.emit(100)
            self.success = True

        except Exception as e:
            self.error.emit(f"Download error: {e}")
        finally:
            self.dl_finished.emit()


class DownloaderDialog(QMainWindow):
    def __init__(self, urls, destination, file_info="llama.cpp, total ~2MB", parent=None):
        super().__init__(parent)
        self.download_thread = None
        self.urls = urls
        self.destination = destination  # needs absolute full path
        self.file_info = file_info

        self.current_file_index = 0
        self.total_files = 4
        self.filenames = [os.path.basename(unquote(urlparse(url).path)) for url in urls]

        self.resize(386, 220)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowMaximizeButtonHint)
        self.titleBar = CustomTitleBar(self, custom_title="Matcha Chat 2 - Downloader")
        self.setMenuWidget(self.titleBar)
        self.setWindowTitle("Matcha Chat 2")

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        self.setStyleSheet("background:transparent")
        self.windowEffect = services.windows_api_handler.WindowEffect()
        self.windowEffect.setAcrylicEffect(int(self.winId()), gradientColor='00101080')

        central_widget = QWidget(self)
        self.layout = QVBoxLayout(central_widget)

        self.label = QLabel(self.file_info, self)
        self.layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        bar_style = """
        QProgressBar{
            border: 0px solid grey;
            border-radius: 0px;
            text-align: center
        }

        QProgressBar::chunk {
            background-color: #599e5e;
        }
        """
        self.progress_bar.setStyleSheet(bar_style)
        self.layout.addWidget(self.progress_bar)

        self.download_button = QPushButton('Start', self)
        self.download_button.clicked.connect(self.start_download)
        self.layout.addWidget(self.download_button)

        self.cancel_button = QPushButton('Discard', self)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.layout.addWidget(self.cancel_button)

        self.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def start_download(self):
        self.download_next_file()

    def download_next_file(self):
        if self.current_file_index+1 <= self.total_files:
            self.progress_bar.setValue(0)
            url = self.urls[self.current_file_index]
            filename = self.filenames[self.current_file_index]
            self.start_download_thread(url, filename)

    def start_download_thread(self, url, filename):
        if self.download_thread is not None:
            if self.download_thread.isRunning():
                self.download_thread.wait()
        self.download_thread = DownloadThread(url=url, filename=filename)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.dl_finished.connect(self.download_finished)
        self.download_thread.error.connect(self.show_error_message)
        self.download_thread.start()

    def cancel_download(self):
        self.download_thread.cancel_download()
        self.cancel_button.setEnabled(False)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Download Error: ", message)
        self.download_button.setEnabled(True)

    def update_progress(self, value):
        progress_text = f"{self.file_info}, downloading file {self.current_file_index + 1}/{self.total_files}."
        self.progress_bar.setValue(value)
        self.label.setText(progress_text)

    def all_downloads_finished(self):
        QMessageBox.information(self, "Finished!", "All downloads finished!")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def download_finished(self):
        print(f"{self.current_file_index}, {self.urls[self.current_file_index]}, {self.filenames[self.current_file_index]}")
        if self.download_thread.success:
            source_path = os.path.join(os.path.abspath('./temp'), self.filenames[self.current_file_index])
            destination_path = os.path.join(self.destination, self.filenames[self.current_file_index])
            destination_dir = os.path.dirname(destination_path)

            os.makedirs(destination_dir, exist_ok=True)

            shutil.move(source_path, destination_path)
            print("File moved.")
        if self.current_file_index + 1 >= self.total_files:
            # self.download_thread = None
            self.all_downloads_finished()
        else:
            self.current_file_index += 1
            # self.download_thread = None
            self.download_next_file()
