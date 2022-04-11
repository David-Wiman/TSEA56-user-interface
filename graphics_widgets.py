from time import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                               QLabel, QPushButton, QSizePolicy,
                               QStackedWidget, QTableWidget, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from backend import backend_signals, socket
from data import CarData, ManualDriveInstruction


class PlaceHolder(QLabel):
    """ Placeholder widget while app is being developed """

    def __init__(self, name: str):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setText(name)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)


class MapWidget(PlaceHolder):
    """ A map that illustrates where the car is on the track """

    def __init__(self):
        super().__init__("Map")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border: 1px solid grey")


class DataField(QLabel):
    """ Custom label to display car data field """

    def __init__(self, label: str, data, unit: str):
        super().__init__()
        self.label = label
        self.unit = unit

        self.update_data(data)
        self.resize(90, 50)
        self.setStyleSheet("border: 0px")

    def update_data(self, data):
        """ Updates field with new data, but same label and unit """
        label_padded = self.label + ":\t\t"
        if len(self.label) < 8:
            label_padded += "\t"  # Fix alignment for short labels

        self.setText(label_padded + str(data) + " " + self.unit)


class DataWidget(QFrame):
    """ A box which lists the most recent driving data """

    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(250)

        layout = QVBoxLayout(self)

        # Widget title label
        data_lbl = QLabel(self)
        data_lbl.resize(70, 50)
        data_lbl.setText("Data")
        data_lbl.setStyleSheet("border: 0px")
        layout.addWidget(data_lbl)

        # Widget data labels
        self.labels: list[DataField] = []
        self.labels.append(DataField("Körtid", 0, "s"))
        self.labels.append(DataField("Gaspådrag", 0, ""))
        self.labels.append(DataField("Styrutslag", 0, ""))
        self.labels.append(DataField("Hastighet", 0, "cm/s"))
        self.labels.append(DataField("Körsträcka", 0, "cm"))
        self.labels.append(DataField("Hinderavstånd", 0, "cm"))
        self.labels.append(DataField("Lateral", 0, "cm"))
        self.labels.append(DataField("Vinkelavvikelse", 0, "rad"))

        for label in self.labels:
            # Add data labels to screen
            layout.addWidget(label)

        self.setStyleSheet("border: 1px solid grey")

        # Automatically update data when it arrives from socket
        backend_signals().new_car_data.connect(self.update_data)

    def update_data(self, data: CarData):
        self.labels[0].update_data(data.time)
        self.labels[1].update_data(data.throttle)
        self.labels[2].update_data(data.steering)
        self.labels[3].update_data(data.velocity)
        self.labels[4].update_data(data.driven_distance)
        self.labels[5].update_data(data.obsticle_distance)
        self.labels[6].update_data(data.lateral_position)


class PlanWidget(PlaceHolder):
    """ A box that lists the currently planned driving instructions """

    def __init__(self):
        super().__init__("Plan")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border: 1px solid grey")


class LogWidget(QTabWidget):
    """ A console that displays logs recieved from the car """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        logger = QTableWidget(self)
        logger.setRowCount(24)
        logger.setColumnCount(4)
        logger.setHorizontalHeaderLabels(
            ("Message;Severity;Node;Timestamp").split(";"))
        logger.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        self.addTab(logger, "Logg")


class ControlsWidget(QStackedWidget):
    """ A controls area where the user can control the car. Has different modes. """

    widget_index = {"manual": 0, "semi": 1, "auto": 2}

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        manual_mode = ManualMode()
        semi_mode = PlaceHolder("Semi autonomous controls")
        auto_mode = PlaceHolder("Fully autonomous controls")

        self.insertWidget(self.widget_index["manual"], manual_mode)
        self.insertWidget(self.widget_index["semi"], semi_mode)
        self.insertWidget(self.widget_index["auto"], auto_mode)

        self.setStyleSheet("border: 1px solid grey")

    def set_index(self, mode):
        self.setCurrentIndex(self.widget_index[mode])


class ManualMode(QWidget):
    """ The buttons needed for manual driving """

    MAX_SEND_RATE = 1/10  # Frequency (Hz)
    CAR_ACC = 100         # Max throttle
    FULL_STEER = 280      # Max steer (right)
    HALF_STEER = 100      # Half steer

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # create push button - parameter
        param_btn = QPushButton("Parametrar", self)
        param_btn.setFixedSize(110, 60)

        # create push button - stop
        stop_btn = QPushButton('STOP', self)
        stop_btn.setFixedSize(110, 110)
        stop_btn.setStyleSheet(
            "background-color: red; border : 2px solid darkred;font-size: 20px;font-family: Arial")
        stop_btn.clicked.connect(socket().hard_stop_car)

        layout = QHBoxLayout(self)

        layout_left = QVBoxLayout()
        layout_right = QGridLayout()
        layout_left.addWidget(param_btn)
        layout_left.addWidget(stop_btn)

        self.create_drive_buttons(layout_right)
        self.setup_keyboard_shortcuts()

        layout.addLayout(layout_left)
        layout.addLayout(layout_right)

        self.timer = time()

    def create_drive_buttons(self, layout):
        size_policy = QSizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)
        size_policy.setWidthForHeight(True)

        fwrd = QToolButton()
        fwrd.clicked.connect(self.send_fwrd)
        fwrd.setAutoRepeat(True)
        fwrd.setAutoRepeatInterval(self.MAX_SEND_RATE * 250)
        fwrd.setArrowType(Qt.UpArrow)
        fwrd.setSizePolicy(size_policy)
        layout.addWidget(fwrd, 0, 1)

        bwrd = QToolButton()
        bwrd.clicked.connect(self.send_bwrd)
        bwrd.setAutoRepeat(True)
        bwrd.setAutoRepeatInterval(self.MAX_SEND_RATE * 250)
        bwrd.setArrowType(Qt.DownArrow)
        bwrd.setSizePolicy(size_policy)
        layout.addWidget(bwrd, 1, 1)

        left = QToolButton()
        left.clicked.connect(self.send_left)
        left.setAutoRepeat(True)
        left.setAutoRepeatInterval(self.MAX_SEND_RATE * 250)
        left.setArrowType(Qt.LeftArrow)
        left.setSizePolicy(size_policy)
        layout.addWidget(left, 1, 0)

        right = QToolButton()
        right.clicked.connect(self.send_right)
        right.setAutoRepeat(True)
        right.setAutoRepeatInterval(self.MAX_SEND_RATE * 250)
        right.setArrowType(Qt.RightArrow)
        right.setSizePolicy(size_policy)
        layout.addWidget(right, 1, 2)

        fwrd_right = QToolButton()
        fwrd_right.clicked.connect(self.send_fwrd_right)
        fwrd_right.setAutoRepeat(True)
        fwrd_right.setAutoRepeatInterval(self.MAX_SEND_RATE * 250)
        fwrd_right.setArrowType(Qt.NoArrow)
        fwrd_right.setSizePolicy(size_policy)
        layout.addWidget(fwrd_right, 0, 2)

        fwrd_left = QToolButton()
        fwrd_left.clicked.connect(self.send_fwrd_left)
        fwrd_left.setAutoRepeat(True)
        fwrd_left.setAutoRepeatInterval(self.MAX_SEND_RATE * 250)
        fwrd_left.setArrowType(Qt.NoArrow)
        fwrd_left.setSizePolicy(size_policy)
        layout.addWidget(fwrd_left, 0, 0)

    def setup_keyboard_shortcuts(self):
        """ Create WASD keybord shortcuts """
        shortcut_fwrd = QShortcut(QKeySequence("w"), self)
        shortcut_fwrd.activated.connect(self.send_fwrd)

        shortcut_bwrd = QShortcut(QKeySequence("s"), self)
        shortcut_bwrd.activated.connect(self.send_bwrd)

        shortcut_right = QShortcut(QKeySequence("d"), self)
        shortcut_right.activated.connect(self.send_right)

        shortcut_left = QShortcut(QKeySequence("a"), self)
        shortcut_left.activated.connect(self.send_left)

        shortcut_fwrd_right = QShortcut(QKeySequence("e"), self)
        shortcut_fwrd_right.activated.connect(self.send_fwrd_right)

        shortcut_fwrd_left = QShortcut(QKeySequence("q"), self)
        shortcut_fwrd_left.activated.connect(self.send_fwrd_left)

    def send_fwrd(self):
        self.send_drive_instruction(ManualDriveInstruction(self.CAR_ACC, 0))

    def send_bwrd(self):
        self.send_drive_instruction(ManualDriveInstruction(0, 0))

    def send_right(self):
        self.send_drive_instruction(
            ManualDriveInstruction(self.CAR_ACC, self.FULL_STEER))

    def send_left(self):
        self.send_drive_instruction(
            ManualDriveInstruction(self.CAR_ACC, -self.FULL_STEER))

    def send_fwrd_right(self):
        self.send_drive_instruction(
            ManualDriveInstruction(self.CAR_ACC, self.HALF_STEER))

    def send_fwrd_left(self):
        self.send_drive_instruction(
            ManualDriveInstruction(self.CAR_ACC, -self.HALF_STEER))

    def send_drive_instruction(self, drive_instruction: ManualDriveInstruction):
        # Sends drive intruction at approximately MAX_SEND_RATE (Hz)
        new_time = time()
        if new_time - self.timer > self.MAX_SEND_RATE:
            try:
                socket().send_message(drive_instruction.to_json())
            except ConnectionError as e:
                print("ERROR:", e)

            self.timer = new_time  # Reset timer


class ButtonsWidget(QWidget):
    """ Buttons that can change which drivning mode is used to steer the car """

    def __init__(self, change_mode=lambda: None):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)

        manual_btn = ModeButton("Manuell", lambda: change_mode("manual"))
        semi_btn = ModeButton("Semiautonom", lambda: change_mode("semi"))
        full_btn = ModeButton("Helautonom", lambda: change_mode("auto"))

        layout.addWidget(manual_btn)
        layout.addWidget(semi_btn)
        layout.addWidget(full_btn)


class ModeButton(QPushButton):
    """ A button that can toggle driving modes for the ControlWidget """

    def __init__(self, label: str, action=lambda: None):
        super().__init__()
        self.setMinimumSize(110, 45)

        self.setText(label)
        self.clicked.connect(lambda: self.action(action))

    def action(self, action):
        action()
