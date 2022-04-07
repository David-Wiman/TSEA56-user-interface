from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                               QLabel, QPushButton, QSizePolicy,
                               QStackedWidget, QTableWidget, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from backend import send_message, websocket
from data import DriveInstruction


class PlaceHolder(QLabel):
    """Placeholder widget while app is being developed"""

    def __init__(self, name: str):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setText(name)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)


class MapWidget(PlaceHolder):
    """A map that illustrates where the car is on the track"""

    def __init__(self):
        super().__init__("Map")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border: 1px solid grey")


class DataWidget(QFrame):
    """A box which lists the most recent driving data"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(250)

        layout = QVBoxLayout(self)

        # creating label - Data
        data_lbl = QLabel(self)
        data_lbl.resize(70, 50)
        data_lbl.setText("Data")
        data_lbl.setStyleSheet("border: 0px")
        layout.addWidget(data_lbl)

        # creating label - Drive Time
        drive_time_lbl = QLabel(self)
        drive_time_lbl.resize(90, 50)
        drive_time_lbl.setText("Körtid:")
        drive_time_lbl.setStyleSheet("border: 0px")
        layout.addWidget(drive_time_lbl)

        # creating label - Gas
        gas_lbl = QLabel(self)
        gas_lbl.resize(90, 50)
        gas_lbl.setText("Gaspådrag:")
        gas_lbl.setStyleSheet("border: 0px")
        layout.addWidget(gas_lbl)

        # creating label - Strearing
        stear_lbl = QLabel(self)
        stear_lbl.resize(90, 50)
        stear_lbl.setText("Styrutslag:")
        stear_lbl.setStyleSheet("border: 0px")
        layout.addWidget(stear_lbl)

        # creating label - Velocity
        vel_lbl = QLabel(self)
        vel_lbl.resize(90, 50)
        vel_lbl.setText("Hastighet:")
        vel_lbl.setStyleSheet("border: 0px")
        layout.addWidget(vel_lbl)

        # creating label - Distance
        dist_lbl = QLabel(self)
        dist_lbl.resize(90, 50)
        dist_lbl.setText("Körsträcka:")
        dist_lbl.setStyleSheet("border: 0px")
        layout.addWidget(dist_lbl)

        # creating label - lateral dist
        lat_lbl = QLabel(self)
        lat_lbl.resize(90, 50)
        lat_lbl.setText("Lateral:")
        lat_lbl.setStyleSheet("border: 0px")
        layout.addWidget(lat_lbl)

        self.setStyleSheet("border: 1px solid grey")


class PlanWidget(PlaceHolder):
    """A box that lists the currently planned driving instructions"""

    def __init__(self):
        super().__init__("Plan")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border: 1px solid grey")


class LogWidget(QTabWidget):
    """A console that displays logs recieved from the car"""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        logger = QTableWidget(self)
        logger.setRowCount(24)
        logger.setColumnCount(4)
        logger.setHorizontalHeaderLabels(
            ("Message;Severity;Node;Timestamp").split(";"))
        logger.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # creating tabWidget to insert logger osv
        self.addTab(logger, "Logg")


class ControlsWidget(QStackedWidget):
    """A controls area where the user can control the car. Has different modes."""

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
        #print("Changing controls to " + mode + " mode!")
        self.setCurrentIndex(self.widget_index[mode])


class ManualMode(QWidget):

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
        stop_btn.clicked.connect(lambda: print("STOP!"))

        layout = QHBoxLayout(self)

        layout_left = QVBoxLayout()
        layout_right = QGridLayout()
        layout_left.addWidget(param_btn)
        layout_left.addWidget(stop_btn)

        self.create_drive_buttons(layout_right)
        self.setup_keyboard_shortcuts()

        layout.addLayout(layout_left)
        layout.addLayout(layout_right)

    def create_drive_buttons(self, layout):
        size_policy = QSizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)
        size_policy.setWidthForHeight(True)

        fwrd = QToolButton()
        fwrd.clicked.connect(self.send_fwrd)
        fwrd.setArrowType(Qt.UpArrow)
        fwrd.setSizePolicy(size_policy)
        layout.addWidget(fwrd, 0, 1)

        bwrd = QToolButton()
        bwrd.clicked.connect(self.send_bwrd)
        bwrd.setArrowType(Qt.DownArrow)
        bwrd.setSizePolicy(size_policy)
        layout.addWidget(bwrd, 1, 1)

        left = QToolButton()
        left.clicked.connect(self.send_left)
        left.setArrowType(Qt.LeftArrow)
        left.setSizePolicy(size_policy)
        layout.addWidget(left, 1, 0)

        right = QToolButton()
        right.clicked.connect(self.send_right)
        right.setArrowType(Qt.RightArrow)
        right.setSizePolicy(size_policy)
        layout.addWidget(right, 1, 2)

        fwrd_right = QToolButton()
        fwrd_right.clicked.connect(self.send_fwrd_right)
        fwrd_right.setArrowType(Qt.NoArrow)
        fwrd_right.setSizePolicy(size_policy)
        layout.addWidget(fwrd_right, 0, 2)

        fwrd_left = QToolButton()
        fwrd_left.clicked.connect(self.send_fwrd_left)
        fwrd_left.setArrowType(Qt.NoArrow)
        fwrd_left.setSizePolicy(size_policy)
        layout.addWidget(fwrd_left, 0, 0)

    def setup_keyboard_shortcuts(self):
        """ Create WASD keybord shortcuts"""
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
        fwrd = DriveInstruction(0.3, 0)
        websocket().send_message(fwrd.to_json("ManualDriveInstruction"))

    def send_bwrd(self):
        bwrd = DriveInstruction(-0.1, 0)
        websocket().send_message(bwrd.to_json("ManualDriveInstruction"))

    def send_right(self):
        right = DriveInstruction(0.15, 0.8)
        websocket().send_message(right.to_json("ManualDriveInstruction"))

    def send_left(self):
        left = DriveInstruction(0.15, -0.8)
        websocket().send_message(left.to_json("ManualDriveInstruction"))

    def send_fwrd_right(self):
        fwrd_right = DriveInstruction(0.2, 0.5)
        websocket().send_message(fwrd_right.to_json("ManualDriveInstruction"))

    def send_fwrd_left(self):
        fwrd_left = DriveInstruction(0.2, -0.5)
        websocket().send_message(fwrd_left.to_json("ManualDriveInstruction"))


class ButtonsWidget(QWidget):
    """Buttons that can change which drivning mode is used to steer the car"""

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
    """A button that can toggle driving modes for the ControlWidget"""

    def __init__(self, label: str, action=lambda: None):
        super().__init__()
        #self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(110, 45)

        self.setText(label)
        self.clicked.connect(lambda: self.action(action))

    def action(self, action):
        # self.toggle_pressed_style()
        action()
