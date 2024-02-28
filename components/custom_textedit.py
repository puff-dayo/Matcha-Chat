import os

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import (QTextCursor, QImage)
from PySide6.QtWidgets import (QTextEdit)


class CustomTextEdit(QTextEdit):
    image_found = Signal(str)
    enter_pressed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self.enter_pressed.emit("")

    def moveCursorToEnd(self):
        self.moveCursor(QTextCursor.End)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasImage():
            temp_dir = './temp'
            os.makedirs(temp_dir, exist_ok=True)
            image_path = os.path.join(temp_dir, 'temp_image.jpg')

            image = source.imageData()
            if isinstance(image, QImage):
                image.save(image_path, 'JPEG')
                self.image_found.emit(image_path)
        if source.hasText():
            plain_text = source.text()
            self.insertPlainText(plain_text)
        else:
            super().insertFromMimeData(source)
