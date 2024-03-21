from PySide6.QtCore import QObject, Signal
from win11toast import toast


def show_notification(title='Hello', description='This is a hello.'):
    toast(title, description, duration='long',
          on_click=lambda args: on_view())


def on_dismiss():
    pass

def on_view():
    reply_signal.pop_view.emit("0")


class ViewSignal(QObject):
    pop_view = Signal(str)


reply_signal = ViewSignal()

