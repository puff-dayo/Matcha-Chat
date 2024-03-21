from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (QVBoxLayout,
                               QWidget, QLabel, QHBoxLayout, QSlider, QSpinBox,
                               QAbstractSpinBox, QDoubleSpinBox, QSizePolicy)


class CustomSlider(QWidget):
    def __init__(self, name, defaultValue, minValue, midValue, maxValue, toolTip, tickInterval=1):
        super().__init__()

        self.updating_from_spin = False

        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(5, 0, 5, 0)

        label = QLabel(name)
        label.setAlignment(Qt.AlignVCenter)
        label.setMinimumWidth(90)
        label.setMaximumWidth(90)

        self.slider = QSlider(Qt.Horizontal)
        self.minValue = minValue
        self.midValue = midValue
        self.maxValue = maxValue
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(self.valueToSliderPosition(defaultValue))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(tickInterval)
        self.slider.setToolTip(f"{toolTip}")
        self.slider.valueChanged.connect(self.updateLabel)

        sliderStyleSheet = """
                QSlider::groove:horizontal {
                    border: 0px solid #999999;
                    height: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b1b1b1, stop:1 #c4c4c4);
                    margin: 0px 0;
                }
                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #599e5e, stop:1 #599e5e);
                    border: 0px solid #5c5c5c;
                    border-radius: 0px;
                    width: 18px;
                    margin: -2px 0;
                }
                QSlider::add-page:horizontal {
                    background: #575757;
                }
                QSlider::sub-page:horizontal {
                    background: #599e5e;
                }
                """
        self.slider.setStyleSheet(sliderStyleSheet)
        self.slider.setMinimumWidth(120)

        self.spin = QSpinBox()
        self.spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin.setStyleSheet("""
            QSpinBox {
                border: 0px solid gray;
                border-radius: 0px;
            }
        """)
        self.spin.setMaximum(maxValue)
        self.spin.setMinimum(minValue)
        self.spin.setMinimumWidth(60)
        self.spin.setMaximumWidth(60)
        self.spin.setAlignment(Qt.AlignVCenter)
        self.spin.valueChanged.connect(self.updateSlider)

        palette = self.spin.palette()
        palette.setColor(QPalette.Highlight, QColor("#5bb481"))
        self.spin.setPalette(palette)

        hbox.addWidget(label)
        hbox.addStretch()
        hbox.addWidget(self.slider)
        hbox.addStretch()
        hbox.addWidget(self.spin)

        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        hbox.setStretchFactor(label, 1)
        hbox.setStretchFactor(self.slider, 4)
        hbox.setStretchFactor(self.spin, 1)

        self.spin.setValue(defaultValue)

    def valueToSliderPosition(self, value):
        if value <= self.midValue:
            return 50 * float(value - self.minValue) / (self.midValue - self.minValue)
        else:
            return 50 + 50 * float(value - self.midValue) / (self.maxValue - self.midValue)

    def sliderPositionToValue(self, position):
        if position <= 50:
            return int(round(self.minValue + (self.midValue - self.minValue) * (float(position) / 50)))
        else:
            return int(round(self.midValue + (self.maxValue - self.midValue) * ((float(position) - 50) / 50)))

    def updateLabel(self, position):
        if not self.updating_from_spin:
            value = self.sliderPositionToValue(position)
            self.spin.setValue(int(value))

    def updateSlider(self, value):
        self.updating_from_spin = True
        position = self.valueToSliderPosition(value)
        self.slider.setValue(position)
        self.updating_from_spin = False

    def setValue(self, value):
        self.updating_from_spin = True
        self.slider.setValue(self.valueToSliderPosition(value))
        self.spin.setValue(value)
        self.updating_from_spin = False

    def value(self):
        return self.spin.value()


class CustomSliderDouble(QWidget):
    def __init__(self, name, defaultValue, minValue, maxValue, toolTip, tickInterval=1):
        super().__init__()

        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(5, 0, 5, 0)

        label = QLabel(name)
        label.setAlignment(Qt.AlignVCenter)
        label.setMinimumWidth(90)
        label.setMaximumWidth(90)

        self.slider = QSlider(Qt.Horizontal)
        self.minValue = minValue
        self.maxValue = maxValue
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(self.valueToSliderPosition(defaultValue))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(tickInterval)
        self.slider.setToolTip(f"{toolTip}")
        self.slider.valueChanged.connect(self.updateLabel)

        sliderStyleSheet = """
                QSlider::groove:horizontal {
                    border: 0px solid #999999;
                    height: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b1b1b1, stop:1 #c4c4c4);
                    margin: 0px 0;
                }
                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #599e5e, stop:1 #599e5e);
                    border: 0px solid #5c5c5c;
                    border-radius: 0px;
                    width: 18px;
                    margin: -2px 0;
                }
                QSlider::add-page:horizontal {
                    background: #575757;
                }
                QSlider::sub-page:horizontal {
                    background: #599e5e;
                }
                """
        self.slider.setStyleSheet(sliderStyleSheet)

        slider_box = QVBoxLayout()
        slider_box.setAlignment(Qt.AlignVCenter)
        slider_box.addWidget(self.slider)

        self.spin = QDoubleSpinBox()
        self.spin.setSingleStep(0.01)
        self.spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin.setStyleSheet("""
            QSpinBox {
                border: 0px solid gray;
                border-radius: 0px;
            }
        """)
        self.spin.setMaximum(maxValue)
        self.spin.setMinimum(minValue)
        self.spin.setAlignment(Qt.AlignVCenter)
        self.spin.valueChanged.connect(self.updateSlider)

        palette = self.spin.palette()
        palette.setColor(QPalette.Highlight, QColor("#5bb481"))
        self.spin.setPalette(palette)

        self.spin.setMinimumWidth(60)
        self.spin.setMaximumWidth(60)

        hbox.addWidget(label)
        hbox.addStretch()
        hbox.addWidget(self.slider)
        hbox.addStretch()
        hbox.addWidget(self.spin)

        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        hbox.setStretchFactor(label, 1)
        hbox.setStretchFactor(self.slider, 4)
        hbox.setStretchFactor(self.spin, 1)

        self.spin.setValue(defaultValue)

    def valueToSliderPosition(self, value):
        return 100 * (value - self.minValue) / (self.maxValue - self.minValue)

    def sliderPositionToValue(self, position):
        return (self.maxValue - self.minValue) * 0.01 * position + self.minValue

    def updateLabel(self, position):
        value = self.sliderPositionToValue(position)
        self.spin.setValue(value)

    def updateSlider(self, value):
        position = self.valueToSliderPosition(value)
        position = round(position, 2)
        self.slider.setValue(position)

    def setValue(self, value):
        self.slider.setValue(self.valueToSliderPosition(value))
        self.spin.setValue(value)

    def value(self):
        return self.spin.value()