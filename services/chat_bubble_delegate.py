from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QPainter, QFont, QFontMetrics, QPainterPath, QBrush, QColor, QPen
from PySide6.QtWidgets import QStyledItemDelegate


class ChatBubbleDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vertical_spacing = 10
        self.horizontal_padding = 20
        self.vertical_padding = 10  # Adjusted inside bubble
        self.sender_height = 20

    def paint(self, painter, option, index):
        text = index.model().data(index, Qt.DisplayRole)
        color = index.model().data(index, Qt.BackgroundRole)
        alignment = index.model().data(index, Qt.TextAlignmentRole)
        sender = index.model().data(index, Qt.UserRole)
        sender = " " + sender if alignment == 'Left' else sender + " "

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Calculate text bounding rect
        max_width = option.rect.width() * 0.75
        text_bounding_rect = fm.boundingRect(0, 0, max_width - self.horizontal_padding * 2, 10000, Qt.TextWordWrap,
                                             text)

        # Calculate bubble size and position
        bubble_width = text_bounding_rect.width() + self.horizontal_padding * 2
        bubble_height = text_bounding_rect.height() + self.vertical_padding * 2
        bubble_x = option.rect.left() if alignment == 'Left' else option.rect.right() - bubble_width
        bubble_y = option.rect.top() + self.sender_height

        shadow_offset = 3
        shadow_color = QColor(0, 0, 0, 32)
        shadow_rect = QRectF(bubble_x + shadow_offset, bubble_y + shadow_offset, bubble_width, bubble_height)
        path_shadow = QPainterPath()
        path_shadow.addRoundedRect(shadow_rect, 10, 10)
        painter.fillPath(path_shadow, QBrush(shadow_color))

        bubble_rect = QRectF(option.rect.left(), option.rect.top() + self.sender_height, bubble_width, bubble_height)
        if alignment == 'Right':
            bubble_rect.moveRight(option.rect.right())

        # Draw bubble
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, 10, 10)
        painter.fillPath(path, QBrush(color))

        # Draw sender name
        sender_name_pos = bubble_rect.left() if alignment == 'Left' else bubble_rect.right() - fm.width(sender)
        sender_rect = QRectF(sender_name_pos, option.rect.top(), bubble_width, self.sender_height)
        painter.setPen(QPen(Qt.white))
        painter.drawText(sender_rect, Qt.AlignLeft | Qt.AlignVCenter, sender)

        # Draw message text
        text_draw_rect = QRectF(bubble_rect.left() + self.horizontal_padding, bubble_rect.top() + self.vertical_padding,
                                bubble_width - self.horizontal_padding * 2, bubble_height - self.vertical_padding * 2)
        painter.setPen(QPen(Qt.black))
        painter.drawText(text_draw_rect, Qt.TextWordWrap, text)

        painter.restore()

    def sizeHint(self, option, index):
        text = index.model().data(index, Qt.DisplayRole)
        font = QFont("Segoe UI", 12)
        fm = QFontMetrics(font)
        max_width = option.rect.width() * 0.75
        text_bounding_rect = fm.boundingRect(0, 0, max_width - self.horizontal_padding * 2, 10000, Qt.TextWordWrap,
                                             text)
        bubble_height = text_bounding_rect.height() + self.vertical_padding * 2 + self.sender_height + self.vertical_spacing * 2
        return QSize(int(max_width), int(bubble_height))