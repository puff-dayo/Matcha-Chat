import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton


class CustomButton(QPushButton):
    def __init__(self, icon_type, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(46, 30))
        if icon_type == "1":
            self.setIcon(qta.icon('fa5s.minus', color='#e9ae21'))
            self.setIconSize(QSize(13, 13))
        elif icon_type == "2":
            self.setIcon(qta.icon('fa5s.times', color='#e9726d'))
            self.setIconSize(QSize(15, 15))
        self.setStyleSheet("QPushButton {background-color: transparent; border: none;}"
                           "QPushButton:hover {background-color: lightgray;}"
                           "QPushButton:pressed {background-color: gray;}")


class CustomTitleBar(QWidget):
    def __init__(self, parent=None, custom_title="  Matcha Chat 2"):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.custom_title = custom_title

        self.titleLabel = QLabel(f"  {custom_title}")
        self.titleLabel.setFixedHeight(30)
        self.layout.addWidget(self.titleLabel, 1)

        self.minimizeButton = CustomButton("1")
        self.minimizeButton.clicked.connect(self.onMinimizeClicked)
        self.layout.addWidget(self.minimizeButton)

        self.closeButton = CustomButton("2")
        self.closeButton.clicked.connect(self.onCloseClicked)
        self.layout.addWidget(self.closeButton)

        self.parent().installEventFilter(self)
        self.startPos = None

    def onMinimizeClicked(self):
        self.window().showMinimized()

    def onCloseClicked(self):
        self.window().close()

    def mousePressEvent(self, event: QMouseEvent):
        self.startPos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.startPos:
            delta = event.globalPos() - self.startPos
            self.window().move(self.window().pos() + delta)
            self.startPos = event.globalPos()
