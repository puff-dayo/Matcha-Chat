import os
import shutil
import zipfile
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
    finished = Signal()
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
                    for chunk in r.iter_content(chunk_size=8192):
                        if self.is_canceled:
                            self.finished.emit()
                            return
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
                            self.progress.emit(min(int(bytes_downloaded / total_size * 100), 100))

            self.progress.emit(100)
            self.success = True

        except Exception as e:
            self.error.emit(f"Download error: {e}")
        finally:
            self.finished.emit()


class DownloaderDialog(QMainWindow):
    def __init__(self, url, destination, file_info="llama.cpp, total ~2MB", unzip=False, parent=None):
        super().__init__(parent)
        self.url = url
        self.destination = destination  # needs absolute full path
        self.need_unzip = unzip
        self.file_info = file_info

        parsed_url = urlparse(self.url)
        self.filename = os.path.basename(unquote(parsed_url.path))

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

        # If file exist
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(QLabel("⚠️ File already exists.\nDo you want to resume (or overwrite)?"))

        hbox = QHBoxLayout()
        resume_button = QPushButton("Try Resume")
        resume_button.clicked.connect(self.do_resume_download)
        overwrite_button = QPushButton("Overwrite")
        overwrite_button.clicked.connect(self.do_overwrite_download)

        hbox.addWidget(resume_button)
        hbox.addWidget(overwrite_button)

        self.vbox.addLayout(hbox)
        self.setCentralWidget(central_widget)

    def do_download(self):
        self.download_thread = DownloadThread(url=self.url, filename=self.filename)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.show_error_message)
        self.download_thread.start()
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

    def restore_ui(self):
        self.download_button = QPushButton('Start', self)
        self.download_button.clicked.connect(self.start_download)
        self.layout.addWidget(self.download_button)

        self.cancel_button = QPushButton('Discard', self)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.layout.addWidget(self.cancel_button)

        self.remove_layout(self.vbox)

    def remove_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                self.remove_layout(item.layout())
        layout.deleteLater()

    def do_resume_download(self):
        self.restore_ui()
        self.do_download()

    def do_overwrite_download(self):
        self.restore_ui()
        try:
            os.remove(os.path.join(os.path.abspath('./temp'), self.filename))
        except FileNotFoundError:
            pass
        self.do_download()

    def start_download(self):
        file_exists = os.path.exists(os.path.join(os.path.abspath('./temp'), self.filename))
        if file_exists:
            self.layout.removeWidget(self.download_button)
            self.download_button.setParent(None)
            self.download_button.deleteLater()

            self.layout.removeWidget(self.cancel_button)
            self.cancel_button.setParent(None)
            self.cancel_button.deleteLater()

            self.layout.addLayout(self.vbox)
        else:
            self.do_download()

    def cancel_download(self):
        self.download_thread.cancel_download()
        self.cancel_button.setEnabled(False)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Download Error: ", message)
        self.download_button.setEnabled(True)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def download_finished(self):
        if self.download_thread.success:
            if self.need_unzip:
                try:
                    self.extract_files()
                    msg = "Download and extraction finished!"
                    QMessageBox.information(self, "Finished!", msg)
                except Exception as e:
                    self.show_error_message(f"Extraction error: {e}")
            else:
                msg = "Download finished!"
                QMessageBox.information(self, "Finished!", msg)
                source_path = os.path.join(os.path.abspath('./temp'), self.filename)
                shutil.move(source_path, self.destination)
                print("File moved.")
        else:
            QMessageBox.information(self, "Information", "Download was canceled or unsuccessful.")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def extract_files(self):
        pkgs_directory = os.path.abspath('./backend')
        os.makedirs(pkgs_directory, exist_ok=True)

        source_zip_path = os.path.join(os.path.abspath('./temp'), self.filename)

        if os.path.exists(source_zip_path) and source_zip_path.endswith('.zip'):
            with zipfile.ZipFile(source_zip_path, 'r') as zip_ref:
                zip_ref.extractall(pkgs_directory)
