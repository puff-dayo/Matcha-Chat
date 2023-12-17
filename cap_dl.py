import os

import requests
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QVBoxLayout,
                               QPushButton, QProgressBar, QDialog, QLabel, QMessageBox)


class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal()
    error = Signal(str)

    def __init__(self, urls, dests):
        super().__init__()
        self.urls = urls
        self.dests = dests
        self.is_canceled = False

    def cancel_download(self):
        self.is_canceled = True

    def run(self):
        temp_directory = os.path.abspath('./models')
        os.makedirs(temp_directory, exist_ok=True)

        try:
            for i, url in enumerate(self.urls):
                headers = {}
                dest = os.path.join(temp_directory, self.dests[i])

                if os.path.exists(dest):
                    bytes_downloaded = os.path.getsize(dest)
                    headers['Range'] = f'bytes={os.path.getsize(dest)}-'
                else:
                    bytes_downloaded = 0

                with requests.get(url, stream=True, headers=headers, timeout=10) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    if 'content-range' in r.headers:
                        total_size = int(r.headers.get('content-range').split('/')[1])

                    print(dest)

                    with open(dest, 'ab') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if self.is_canceled:
                                self.finished.emit()
                                return
                            if chunk:
                                f.write(chunk)
                                bytes_downloaded += len(chunk)
                                self.progress.emit(
                                    min(int(bytes_downloaded / total_size * 100), 100))

                self.progress.emit(100)

        except requests.RequestException as e:
            self.error.emit(f"Download error: {e}")
        finally:
            if not self.is_canceled:
                self.finished.emit()


class DownloadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Download Manager")
        self.setGeometry(300, 300, 300, 150)
        layout = QVBoxLayout()

        self.label = QLabel("Download Progress:\n(llava-v1.5-7B-GGUF, total ~4.0GB)", self)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.download_button = QPushButton('Start Download', self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.cancel_button = QPushButton('Cancel Download', self)
        self.cancel_button.clicked.connect(self.cancel_download)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def start_download(self):
        self.urls = ["https://huggingface.co/jartine/llava-v1.5-7B-GGUF/resolve"
                     "/464b6aff708957b47af122b5b666d5ba81b8616b/llava-v1.5-7b-q4-server.llamafile?download=true"]
        self.dests = ["llava-v1.5-7b-q4-server.llamafile.exe"]
        SHA256 = '67e368f87fc3df0a6cf8b566fe9d91adf3695e338e4c87232dc0be164a1b734c'
        self.download_thread = DownloadThread(self.urls, self.dests)
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
        if not self.download_thread.is_canceled:
            try:
                msgg = "Download finished!"
                QMessageBox.information(self, "Finished!", msgg)
            except Exception as e:
                self.show_error_message(f"Extraction error: {e}")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QDialog

    app = QApplication(sys.argv)
    dialog = DownloadDialog()
    dialog.show()
    sys.exit(app.exec())