import os
import re
import sys
from datetime import datetime

import psutil
import qtawesome as qta
from PySide6.QtCore import Qt, QRectF, QSize, Signal, QThread, QPoint
from PySide6.QtGui import (QPainter, QBrush, QColor, QPen, QFont, QPainterPath, QFontMetrics, QPalette, QIcon)
from PySide6.QtGui import (QStandardItemModel, QStandardItem)
from PySide6.QtWidgets import (QApplication, QMainWindow, QListView, QVBoxLayout,
                               QWidget, QPushButton, QSplitter,
                               QGridLayout, QAbstractItemView, QLabel, QHBoxLayout, QFileDialog)
from PySide6.QtWidgets import QStyledItemDelegate

import services.completion as Server
import services.settings_handler as Settings
import services.windows_api_handler
from components.custom_textedit import CustomTextEdit
from components.custom_titlebar import CustomTitleBar
from downloader_window import DownloaderWindow
from services.completion import Worker as CompletionWorker
from settings_window import SettingsWindow
from services.translator import Translator

os.environ["QT_FONT_DPI"] = "100"


class MemoryMonitorThread(QThread):
    update_signal = Signal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            available_memory_gb = psutil.virtual_memory().available / 1073741824
            memory_usage_str = f"{available_memory_gb:.2f}GB"

            cpu_usage = psutil.cpu_percent(interval=None)
            cpu_usage_str = f"{cpu_usage}"

            status_str = f"<font color='#b3b7b7'>CPU:</font> {cpu_usage_str}% <font color='#b3b7b7'> Free RAM:</font> {memory_usage_str}"
            self.update_signal.emit(status_str)

            self.sleep(1)

            # TODO: how to monitor GPU and VRAM.... pynvml?


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


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._dragging = False
        self._resizing = False
        self._drag_position = QPoint()
        self._resize_position = QPoint()

        self.is_server_running = False

        self.multi_paragraph_enabled = True  # Testing TODO
        self.initial_state = None
        self.previous_state = None

        self.setWindowTitle("Matcha Chat 2")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowMaximizeButtonHint)
        self.titleBar = CustomTitleBar(self)
        self.setMenuWidget(self.titleBar)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        self.init_width = 600
        self.init_height = 901
        self.resize(self.init_width, self.init_height)

        self.restore_shadow()
        self.init_ui()
        self.init_chat()
        self.init_thread()
        self.save_init()

        # self.update_translator_settings()

        models_dir = os.path.join(os.getcwd(), 'models')
        translator_models_dir = os.path.join(models_dir, 'translator')
        self.translator = Translator(translator_models_dir)
        self.translator.init_translator()

    def init_chat_view(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 0, 5, 0)

        self.chatListView = QListView()
        self.model = QStandardItemModel()
        self.chatListView.setModel(self.model)
        self.chatListView.setItemDelegate(ChatBubbleDelegate())

        # Set fake smooth scrolling
        self.chatListView.setWordWrap(True)
        self.chatListView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chatListView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chatListView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.chatListView.verticalScrollBar().setSingleStep(15)

        self.layout.addWidget(self.chatListView)

    def send_message(self):
        # Save previous state TODO
        # self.inputText.setEnabled(False)
        try:
            user_input = self.inputText.toPlainText().strip()
            raw_input = user_input
            self.inputText.setText("")
            print("input: " + user_input)

            if self.in_translate:
                user_input = self.translator.translate(text_input=user_input,
                                                       source_lang=self.target,
                                                       target_lang='en')
                print("translated_input: " + user_input)

            self.messages.append({"role": "user", "content": user_input})

            if not self.out_translate:
                raw_input = user_input

            if self.multi_paragraph_enabled is False:
                self.add_message(raw_input, self.user_color, "Right", self.user_name)
            else:
                print("here")
                # if multiline
                # text = user_input.replace(" *", "\n\n*")
                segments = [segment for segment in raw_input.splitlines() if segment.strip()]
                for segment in segments:
                    if segment.startswith(f"{self.ai_name}:"):
                        segment = segment[len(f"{self.ai_name}:"):].strip()
                    # if>
                    self.add_message(segment, self.user_color, "Right", self.user_name)

            model = "gpt-3.5-turbo"

            self.worker = CompletionWorker(self.base_url, model, self.messages, self.temperature)
            self.worker.finished.connect(self.on_response_received)
            self.worker.start()
        except Exception as e:
            print(f"Error sending message: {e}")

    def split_long_text(self, text, max_length=100):
        if len(text) <= max_length:
            return [text]

        split_positions = [m.start() for m in re.finditer(r'(?<=[.?!])[^.?!]*[.?!]', text)]
        for pos in reversed(split_positions):
            if pos + 1 <= max_length:
                return [text[:pos + 1], text[pos + 1:].strip()]

        return [text]

    def update_translator_settings(self):
        trans_settings = Settings.load_translator_settings()
        print(trans_settings['in'])
        self.in_translate = trans_settings['in'] == "1"
        self.out_translate = trans_settings['out'] == "1"
        self.target = trans_settings['target']
        print(f'Saved! {self.in_translate}')

    def on_response_received(self, response, token_count):
        print(f"response: {response}\ntoken:{token_count}")
        self.current_tokens_sum = token_count

        self.worker.quit()

        response_text = response
        if response_text.startswith(f"{self.ai_name}: "):
            response_text = response_text[len(f"{self.ai_name}: "):].strip()
        if response_text.startswith(f"{self.ai_name}:"):
            response_text = response_text[len(f"{self.ai_name}:"):].strip()
        marker = "<|im-end|>"
        if response_text.endswith(marker):
            response_text = response_text[:-len(marker)]

        self.messages.append({"role": "assistant", "content": response_text})

        text = response_text.strip()
        text = text.replace("<br>", "\n\n*")

        if self.multi_paragraph_enabled is False:
            if self.out_translate:
                text = self.translator.translate(text_input=text,
                                             source_lang='en',
                                             target_lang=self.target)
            self.add_message(text, self.ai_color, "Left", self.ai_name)
        else:
            text = text.replace(" *", "\n\n*")
            segments = [segment for segment in text.splitlines() if segment.strip()]
            for segment in segments:
                if segment.startswith(f"{self.ai_name}: "):
                    segment = segment[len(f"{self.ai_name}: "):].strip()
                if segment.startswith(f"{self.ai_name}:"):
                    segment = segment[len(f"{self.ai_name}:"):].strip()

                split_texts = self.split_long_text(segment, 150)
                for split_text in split_texts:
                    if self.out_translate:
                        split_text = self.translator.translate(text_input=split_text,
                                                           source_lang='en',
                                                           target_lang=self.target)
                    self.add_message(split_text, self.ai_color, "Left", self.ai_name)

        self.token_status.setText(f"<font color='#b3b7b7'>Capacity:</font> {self.current_tokens_sum} <font "
                                  f"color='#b3b7b7'>/ {self.tokes_limit}</font>")
        print('Done generate.')

    def open_downloader_window(self):
        self.downloader_window = DownloaderWindow(parent=self)
        # self.dialog.setWindowFlags(self.dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        self.downloader_window.show()

    def open_settings_window(self):
        self.setting_window = SettingsWindow(parent=self)
        self.setting_window.show()

    def save_init(self):
        self.initial_state = self.serialize_model()

    def save_current(self):
        self.previous_state = self.serialize_model()

    def reset(self):
        if self.initial_state is not None:
            self.deserialize_model(self.initial_state)

        self.init_chat()

    def undo(self):
        if self.previous_state is not None:
            self.deserialize_model(self.previous_state)
        self.scroll_to_bottom()

    def serialize_model(self):
        data = []
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            data.append({
                'text': item.data(Qt.DisplayRole),
                'color': item.data(Qt.BackgroundRole).name(),
                'alignment': item.data(Qt.TextAlignmentRole),
                'sender': item.data(Qt.UserRole)
            })
        return data

    def deserialize_model(self, data):
        self.model.clear()
        for item_data in data:
            self.add_message(item_data['text'], QColor(item_data['color']), item_data['alignment'], item_data['sender'])

        self.scroll_to_bottom()

    def init_ui(self):
        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.leftWidget = QWidget()
        self.rightWidget = QWidget()

        # Left layout
        self.gridLayout = QGridLayout(self.leftWidget)

        self.init_chat_view()

        self.toolBarWidget = QWidget(self)
        self.toolBar = QHBoxLayout(self.toolBarWidget)
        self.toolBarWidget.setWindowOpacity(1.0)
        self.init_toolbar()

        self.inputText = CustomTextEdit()
        palette = self.inputText.palette()
        palette.setColor(QPalette.Highlight, QColor("#5bb481"))
        self.inputText.setPalette(palette)
        self.inputText.setMinimumHeight(100)
        self.inputText.setMaximumHeight(125)
        self.inputText.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.inputText.setPlaceholderText(
            'Input your message here.\nMultiple lines are treated as multiple messages.\n(Press Enter to create a new line, and Ctrl+Enter to send.)')
        self.inputText.setFont(QFont("Segoe UI"))
        self.inputText.image_found.connect(self.on_image_found)
        self.inputText.enter_pressed.connect(self.send_message)
        self.inputText.setEnabled(False)

        chatWidget = QWidget()
        chatWidget.setLayout(self.layout)

        bottom_hbox = QHBoxLayout()
        self.status_bar = QLabel('Loading...')
        bottom_hbox.addWidget(self.status_bar)
        bottom_hbox.addStretch()
        token_status_str = f"<font color='#b3b7b7'>Capacity:</font> Halt"
        self.token_status = QLabel(token_status_str)
        bottom_hbox.addWidget(self.token_status)

        self.gridLayout.addWidget(chatWidget, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.toolBarWidget, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.inputText, 2, 0, 1, 1)
        self.gridLayout.addLayout(bottom_hbox, 3, 0, 1, 1)

        self.gridLayout.setRowStretch(0, 4)
        self.gridLayout.setRowStretch(1, 0)
        self.gridLayout.setRowStretch(2, 1)
        self.gridLayout.setRowStretch(3, 0)

        # Set R&L layouts
        self.mainSplitter.addWidget(self.leftWidget)

        self.setCentralWidget(self.mainSplitter)

    def init_thread(self):
        self.thread = MemoryMonitorThread()
        self.thread.update_signal.connect(self.update_memory_usage)
        self.thread.start()

    def update_memory_usage(self, memory_usage_str):
        self.status_bar.setText(memory_usage_str)

    # Blank sender for sys/env message maybe...?
    def add_message(self, text, color, alignment, sender=None):
        item = QStandardItem()
        item.setData(text, Qt.DisplayRole)
        item.setData(color, Qt.BackgroundRole)
        item.setData(alignment, Qt.TextAlignmentRole)
        item.setData(sender, Qt.UserRole)
        self.model.appendRow(item)
        self.scroll_to_bottom()

    def export_chat_history_to_html(self):
        default_filename = datetime.now().strftime("%d-%m-%y") + f" {self.user_name} with {self.ai_name}.html"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chat History",
            default_filename,
            "HTML Files (*.html);;All Files (*)"
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('''
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {
                            background: linear-gradient(to bottom, #000000, #333333);
                            color: white;
                            font-family: Arial, sans-serif;
                        }
                        h1 {
                            text-align: center;
                            margin-top: 20px;
                        }
                        p {
                            margin: 10px;
                        }
                    </style>
                </head>
                <body>
                    <h1>Chat History</h1>\n''')
                for row in range(self.model.rowCount()):
                    item = self.model.item(row)
                    text = item.data(Qt.DisplayRole)
                    color = item.data(Qt.BackgroundRole)
                    alignment = item.data(Qt.TextAlignmentRole)
                    sender = item.data(Qt.UserRole)

                    if alignment == 'Left':
                        align = 'left'
                    elif alignment == 'Right':
                        align = 'right'
                    else:
                        align = 'center'

                    if sender:
                        file.write(f'<p style="color: {color}; text-align: {align};">{sender}: {text}</p>\n')
                    else:
                        file.write(f'<p style="text-align: {align};">{text}<br></p>\n')

                file.write('</body></html>')

    def on_image_found(self):
        pass

    def restore_shadow(self):
        self.setStyleSheet("background:transparent")
        self.windowEffect = services.windows_api_handler.WindowEffect()
        self.windowEffect.setAcrylicEffect(int(self.winId()), gradientColor='00101080')

    def scroll_to_bottom(self):
        if self.model.rowCount() > 0:
            lastIndex = self.model.index(self.model.rowCount() - 1, 0)
            self.chatListView.scrollTo(lastIndex, QAbstractItemView.ScrollHint.EnsureVisible)

    def init_toolbar(self):
        self.record_button = QPushButton()
        self.record_button.setIcon(qta.icon('fa5s.microphone'))
        self.record_button.setToolTip("Speak any language, and auto-translated into English.")
        self.record_button.setIconSize(QSize(18, 18))
        # self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setEnabled(False)

        self.mem_button = QPushButton()
        self.mem_button.setIcon(qta.icon('fa5s.calendar-plus', color='lightgray'))
        self.mem_button.setIconSize(QSize(20, 20))
        self.mem_button.setToolTip("View and record permanent memories.")
        # self.mem_button.clicked.connect(self.show_mem_diag)

        self.photo_button = QPushButton()
        self.photo_button.setIcon(qta.icon('fa5s.image', color='lightgray'))
        self.photo_button.setIconSize(QSize(20, 20))
        # self.photo_button.clicked.connect(self.on_photo_clicked)
        self.photo_button.setToolTip("Send an image into chat.")

        download_button = QPushButton()
        download_button.setIcon(qta.icon('fa5s.file-export', color='lightgray'))
        download_button.setIconSize(QSize(16, 16))
        download_button.clicked.connect(self.export_chat_history_to_html)
        download_button.setToolTip("Save current chat history as a file.")

        self.undo_button = QPushButton()
        self.undo_button.setIcon(qta.icon('fa5s.undo', color='lightgray'))
        self.undo_button.setIconSize(QSize(16, 16))
        # self.undo_button.clicked.connect(self.on_undo_clicked)
        self.undo_button.setToolTip("Undo last sent message.")

        self.delete_button = QPushButton()
        self.delete_button.setIcon(qta.icon('fa5s.trash', color='lightgray'))
        self.delete_button.setIconSize(QSize(18, 18))
        self.delete_button.setToolTip("Clear chat history.")
        self.delete_button.clicked.connect(self.reset)

        settings_button = QPushButton()
        settings_button.setIcon(qta.icon('fa5s.cog', color='lightgray'))
        settings_button.setIconSize(QSize(18, 18))
        settings_button.setToolTip("Pop up settings window.")
        settings_button.clicked.connect(self.open_settings_window)

        self.model_list_button = QPushButton()
        self.model_list_button.setIcon(qta.icon('fa5s.download', color='lightgray'))
        self.model_list_button.setIconSize(QSize(18, 18))
        self.model_list_button.setToolTip("Open model list window.")
        self.model_list_button.clicked.connect(self.open_downloader_window)

        self.server_button = QPushButton()
        self.server_button.setIcon(qta.icon('fa5s.play', color='#fd879a'))
        self.server_button.setIconSize(QSize(18, 18))
        self.server_button.setToolTip("Launch or stop the llama.cpp server.")
        self.server_button.clicked.connect(self.launch_or_stop_server)

        self.photo_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        download_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        self.undo_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        self.delete_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        settings_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        self.record_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        self.mem_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        self.model_list_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        self.server_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")

        self.toolBar.addWidget(self.record_button)
        self.toolBar.addWidget(self.photo_button)
        self.toolBar.addWidget(download_button)
        self.toolBar.addWidget(self.undo_button)
        self.toolBar.addWidget(self.delete_button)
        self.toolBar.addWidget(self.mem_button)

        self.toolBar.addStretch()
        self.toolBar.addWidget(self.server_button)
        self.toolBar.addWidget(self.model_list_button)
        self.toolBar.addWidget(settings_button)

    def launch_or_stop_server(self):
        self.reset()
        self.init_chat()
        if self.is_server_running:
            self.server_button.setIcon(qta.icon('fa5s.play', color='#fd879a'))
            Server.kill()
            self.is_server_running = False
            self.inputText.setEnabled(False)
        else:
            Server.boot()
            self.server_button.setIcon(qta.icon('fa5s.stop', color='lightgray'))
            self.is_server_running = True
            self.inputText.setEnabled(True)

    def init_chat(self):
        self.update_translator_settings()
        self.inputText.setEnabled(False)

        settings = Settings.load_settings()
        prompt_settings = Settings.load_prompt_settings()

        self.user_color = "#6edcbe"
        self.ai_color = "#8dd4f4"
        self.user_name = prompt_settings["user_name"]
        self.ai_name = prompt_settings["ai_name"]
        self.base_url = "http://localhost:35634/v1/chat/completions"
        sys_prompt = prompt_settings["sys_prompt"]
        self.messages = [
            {"role": "system",
             "content": str(sys_prompt)},
        ]

        self.current_tokens_sum = 0
        self.tokes_limit = int(settings["capacity"])
        self.temperature = float(settings["temperature"])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

        elif event.button() == Qt.RightButton:
            self._resizing = True
            self._resize_position = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
        elif self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_position
            self._resize_position = event.globalPosition().toPoint()
            self.resize(self.width() + delta.x(), self.height() + delta.y())
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._resizing = False
        event.accept()


def on_close():
    print('Server shutdown.')
    Server.kill()


if __name__ == '__main__':
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=2'])
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setWindowIcon(QIcon('./icon.png'))
    app.setStyle('Fusion')

    # mainFont = QFont("Segoe UI")
    mainFont = QFont("Segoe UI")
    app.setFont(QFont(mainFont))

    app.aboutToQuit.connect(on_close)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())