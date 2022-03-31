from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QStackedWidget, QVBoxLayout,
                               QWidget)


class ModeButton(QPushButton):
    """A button that can toggle driving modes for the ControlWidget"""

    def __init__(self, label: str, action=lambda: None):
        super().__init__()
        self.setText(label)
        self.clicked.connect(lambda: self.action(action))
        self.pressed = False

    def action(self, action):
        # self.toggle_pressed_style()
        action()

    def toggle_pressed_style(self):
        self.pressed = not self.pressed

        if self.pressed:
            self.setStyleSheet("background: red")
        else:
            self.setStyleSheet("background: grey")


class PlaceHolder(QWidget):
    """Placeholder widget while app is being developed"""

    def __init__(self, name: str):
        super().__init__()

        label = QLabel(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setText(name)
        label.setFrameStyle(QFrame.Panel | QFrame.Sunken)


class MapWidget(QWidget):
    """A map that illustrates where the car is on the track"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.addWidget(PlaceHolder("Map"))


class DataWidget(QWidget):
    """A box which lists the most recent driving data"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.addWidget(PlaceHolder("Data"))


class PlanWidget(QWidget):
    """A box that lists the currently planned driving instructions"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.addWidget(PlaceHolder("Plan"))


class LogWidget(QWidget):
    """A console that displays logs recieved from the car"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.addWidget(PlaceHolder("Log"))


class ControlsWidget(QStackedWidget):
    """A controls area where the user can control the car. Has different modes."""

    widget_index = {"manual": 0, "semi": 1, "auto": 2}

    def __init__(self):
        super().__init__()

        manual_mode = PlaceHolder("Manual controls")
        semi_mode = PlaceHolder("Semi autonomous controls")
        auto_mode = PlaceHolder("Fully autonomous controls")

        self.insertWidget(self.widget_index["manual"], manual_mode)
        self.insertWidget(self.widget_index["semi"], semi_mode)
        self.insertWidget(self.widget_index["auto"], auto_mode)

    def set_index(self, mode):
        #print("Changing controls to " + mode + " mode!")
        self.setCurrentIndex(self.widget_index[mode])


class ButtonsWidget(QWidget):
    """Buttons that can change which drivning mode is used to steer the car"""

    def __init__(self, change_mode=lambda: None):
        super().__init__()

        layout = QHBoxLayout(self)

        manual_btn = ModeButton("Manuell", lambda: change_mode("manual"))
        semi_btn = ModeButton("Semiautonom", lambda: change_mode("semi"))
        full_btn = ModeButton("Helautonom", lambda: change_mode("auto"))

        layout.addWidget(manual_btn)
        layout.addWidget(semi_btn)
        layout.addWidget(full_btn)
