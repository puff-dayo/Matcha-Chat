from PySide6.QtCore import Signal, QThread
from win11toast import toast


class NotificationThread(QThread):
    finished_signal = Signal(str)

    def __init__(self, title, description):
        super().__init__()
        self.title = title
        self.description = description

    def run(self):
        toast(self.title, self.description, duration="long", on_click=lambda args: self.on_view())

    def on_view(self):
        self.finished_signal.emit("Notification viewed.")


def show_notification(title, description, self=None):
    self.thread = NotificationThread(title, description)
    self.thread.finished_signal.connect(lambda: print("Notification viewed"))
    self.thread.start()
