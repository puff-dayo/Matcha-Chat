from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (QVBoxLayout,
                               QMainWindow,
                               QWidget)

import services.windows_api_handler
from services.custom_titlebar import CustomTitleBar


class BaseWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.setCentralWidget(central_widget)
