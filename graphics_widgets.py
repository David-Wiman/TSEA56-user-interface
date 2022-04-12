from time import localtime, time

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPlainTextEdit, QPushButton, QScrollArea,
                               QSizePolicy, QStackedWidget, QStyle, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from backend import backend_signals, socket
from data import (CarData, Direction, ManualDriveInstruction,
                  SemiDriveInstruction)


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

    DATA_FILENAME = "data_output.txt"

    def __init__(self):
        super().__init__()
        self.all_data: list[CarData] = []

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(250)

        layout = QVBoxLayout(self)
        layout_h = QHBoxLayout()  # Top label and save button

        # Widget title label
        data_lbl = QLabel()
        data_lbl.resize(70, 50)
        data_lbl.setText("Data")
        data_lbl.setStyleSheet("border: 0px")
        layout_h.addWidget(data_lbl)

        # Save data button
        save_btn = QPushButton("Spara")
        save_btn.setIcon(QStyle.standardIcon(
            self.style(), QStyle.SP_DialogSaveButton))
        save_btn.resize(90, 90)
        save_btn.setStyleSheet("border: none")
        save_btn.clicked.connect(self.save_data)
        layout_h.addWidget(save_btn)
        layout.addLayout(layout_h)

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
        self.all_data.append(data)

    def save_data(self):
        """ Save all car data to file """
        with open(self.DATA_FILENAME, "w") as file:
            file.write("\n".join([data.to_json() for data in self.all_data]))

        backend_signals().log_msg.emit(
            "INFO", "Saved all car data to \"{}\"".format(self.DATA_FILENAME))


class InstructionWidget(QLabel):
    """ Small widget showing an arrow corresponding to a drive direction """

    def __init__(self, direction: Direction = 1):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(90, 120)

        icon_name = ""
        if direction == Direction.FWRD:
            icon_name = "up_arrow.png"
        elif direction == Direction.LEFT:
            icon_name = "up_arrow.png"
        elif direction == Direction.RIGHT:
            icon_name = "up_arrow.png"

        self.setPixmap(QPixmap("res/" + icon_name))

        self.setStyleSheet("border: none")


class PlanWidget(QScrollArea):
    """ A box that lists the currently planned driving instructions """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.instructions: list[SemiDriveInstruction] = []

        self.queue = QWidget(self)
        self.draw_instructions()

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.queue)

        self.setStyleSheet("border: 1px solid grey")

    def draw_instructions(self):
        layout = QHBoxLayout(self.queue)
        for _ in range(4):
            layout.addWidget(InstructionWidget())
        layout.addStretch(1)  # Left align

    def add_instruction(self, instruction: SemiDriveInstruction):
        self.instructions.append(instruction)

    def remove_instruction(self, id: str):
        """ Removes instruction, if it exists """
        self.instructions = [ins for ins in self.instructions if ins.id != id]

    def clear_all(self):
        """ Remove all instructions and reset widget """
        self.instructions = []
        self.queue = QWidget()
        self.setWidget(self.queue)


class LogWidget(QTabWidget):
    """ A log that displays log data from backend """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.logger = QPlainTextEdit(self)
        self.logger.setReadOnly(True)
        self.text = ""
        backend_signals().log_msg.connect(self.add_log)  # Add log from backend

        self.addTab(self.logger, "Logg")

    def add_log(self, severity, message):
        """ Adds message to the log widget on GUI """
        current_time = \
            str(localtime().tm_hour).zfill(2) + ":" + \
            str(localtime().tm_min).zfill(2) + ":" + \
            str(localtime().tm_sec).zfill(2)

        entry = "[" + current_time + " - " + severity + "]\t" + message
        self.logger.appendPlainText(entry)


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
