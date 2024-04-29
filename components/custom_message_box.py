import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout, QWidget, \
    QLabel

from components.custom_titlebar import CustomTitleBar
from services import windows_api_handler


class CustomMessageBox(QMainWindow):
    def __init__(self, title="Matcha Chat 2", text="Place holder", ok_only=True, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setWindowFlag(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                           | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)

        self.titleBar = CustomTitleBar(self, custom_title=title)
        self.setMenuWidget(self.titleBar)

        self.setStyleSheet("background:transparent")
        self.windowEffect = windows_api_handler.WindowEffect()
        self.windowEffect.setAcrylicEffect(int(self.winId()), gradientColor='00101080')

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.yesButton = QPushButton("Yes")
        self.noButton = QPushButton("No")
        self.okButton = QPushButton("OK")

        for button in [self.yesButton, self.noButton, self.okButton]:
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
            button.setStyleSheet(button_style)

        self.yesButton.setIcon(QIcon.fromTheme("dialog-ok"))
        self.noButton.setIcon(QIcon.fromTheme("dialog-cancel"))
        self.okButton.setIcon(QIcon.fromTheme("dialog-ok"))
        self.okButton.clicked.connect(self.close)

        self.yesButton.setAutoDefault(False)
        self.noButton.setAutoDefault(False)
        self.okButton.setAutoDefault(True)

        layout.addWidget(QLabel(text))

        if not ok_only:
            layout.addWidget(self.yesButton)
            layout.addWidget(self.noButton)
        layout.addWidget(self.okButton)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        self.move(int(screen_width / 2), int(screen_height / 2))

    def getYesButton(self):
        return self.yesButton

    def getNoButton(self):
        return self.noButton

    def getOkButton(self):
        return self.okButton


if __name__ == "__main__":
    app = QApplication([])

    # Create a custom dialog
    dialog = CustomMessageBox("Custom Dialog", "This is a custom dialog example.")

    # Show the dialog
    dialog.show()

    sys.exit(app.exec())
