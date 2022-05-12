from time import localtime, time

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QFormLayout, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                               QScrollArea, QSizePolicy, QStackedWidget,
                               QStyle, QTabWidget, QToolButton, QVBoxLayout,
                               QWidget)

from backend import backend_signals, socket
from config import (ANGLE_OFFSET, CAR_ACC, DATA_PATH, FULL_STEER, HALF_STEER,
                    MAX_SEND_RATE, SPEED_KI, SPEED_KP, STEER_KD, STEER_KP,
                    TURN_KD)
from data import (Direction, DriveData, DriveMission, DrivingMode,
                  ManualDriveInstruction, MapData, ParameterConfiguration,
                  SemiDriveInstruction)
from map_creator import MapCreatorWidget


def LOG(severity: str, message: str):
    """ Logs message with severity to LogWidget"""
    backend_signals().log_msg.emit(severity, message)


class PlaceHolder(QLabel):
    """ Placeholder widget while app is being developed """

    def __init__(self, name: str):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setText(name)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)


class MapWidget(QLabel):
    """ A map that illustrates the track """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.setStyleSheet("border: 1px solid grey; background-color: #A0A0A4")

        self.update_map()
        backend_signals().new_map.connect(self.update_map)

    def update_map(self):
        """ Redraws map """
        map_image = QPixmap("res/" + "map.png")
        map_image = map_image.scaled(self.size(), Qt.KeepAspectRatio,
                                     Qt.SmoothTransformation)
        self.setPixmap(map_image)


class DataWidget(QFrame):
    """ A box which lists the most recent driving data """

    class DataField(QLabel):
        """ Custom label to display car's drive data field """

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

    def __init__(self):
        super().__init__()
        self.all_data: list[DriveData] = []

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
        self.labels: list[self.DataField] = []
        self.labels.append(self.DataField("Körtid", 0, "s"))
        self.labels.append(self.DataField("Gaspådrag", 0, ""))
        self.labels.append(self.DataField("Styrutslag", 0, ""))
        self.labels.append(self.DataField("Hastighet", 0, "cm/s"))
        self.labels.append(self.DataField("Körsträcka", 0, "m"))
        self.labels.append(self.DataField("Hinderavstånd", 0, "cm"))
        self.labels.append(self.DataField("Lateral", 0, "cm"))
        self.labels.append(self.DataField("Vinkelavvikelse", 0, "grader"))

        for label in self.labels:
            # Add data labels to screen
            layout.addWidget(label)

        self.setStyleSheet("border: 1px solid grey")

        # Automatically update data when it arrives from socket
        backend_signals().new_drive_data.connect(self.update_data)

    def update_data(self, data: DriveData):
        self.labels[0].update_data(int(data.elapsed_time / 1000))  # ms-> s
        self.labels[1].update_data(data.throttle)
        self.labels[2].update_data(data.steering)
        self.labels[3].update_data(data.speed / 10)  # mm/s -> cm/s
        self.labels[4].update_data(data.driving_distance / 10)  # dm -> m
        self.labels[5].update_data(data.obstacle_distance)
        self.labels[6].update_data(data.lateral_position)
        self.labels[7].update_data(data.angle)
        self.all_data.append(data)  # Add data to history

    def save_data(self):
        """ Save all drive signals as csv files """

        self.save_signal("throttle",
                         [str(data.throttle) for data in self.all_data])

        self.save_signal("steering",
                         [str(data.steering) for data in self.all_data])

        self.save_signal("speed",
                         [str(data.speed) for data in self.all_data])

        self.save_signal("driving_distance",
                         [str(data.driving_distance) for data in self.all_data])

        self.save_signal("obstacle_distance",
                         [str(data.obstacle_distance) for data in self.all_data])

        self.save_signal("lateral_position",
                         [str(data.lateral_position) for data in self.all_data])

        self.save_signal("angle",
                         [str(data.angle) for data in self.all_data])

        LOG("INFO", "Saved all drive data to folder \"{}\"".format(DATA_PATH))

    def save_signal(self, name, data_list):
        """ Saves list of strings as csv-file with name """
        fname = DATA_PATH + name + ".csv"

        with open(fname, "w") as file:
            file.write(",".join(data_list) + "\n")
            file.write(",".join([str(data.elapsed_time)
                       for data in self.all_data]))
            file.close()
        print("Saved " + name + " data to: " + fname)


class PlanWidget(QStackedWidget):

    def __init__(self):
        super().__init__()

        manual = QWidget()  # Empty plan in manual mode
        semi_mode = SemiPlanWidget()
        auto_mode = AutoPlanWidget()

        self.insertWidget(DrivingMode.MANUAL, manual)
        self.insertWidget(DrivingMode.SEMIAUTO, semi_mode)
        self.insertWidget(DrivingMode.AUTO, auto_mode)

        backend_signals().change_drive_mode.connect(self.switch_mode)

    def switch_mode(self, mode: DrivingMode):
        """ Switches which plan is being displayed """
        self.setCurrentIndex(mode)


class SemiPlanWidget(QScrollArea):
    """ A box that lists the currently planned driving instructions """

    class InstructionWidget(QLabel):
        """ Small widget showing an arrow corresponding to a drive direction """

        def __init__(self, direction: Direction = 1):
            super().__init__()
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.setFixedSize(90, 120)

            # Set icon correspoding to direction
            icon_name = ""
            if direction == Direction.FWRD:
                icon_name = "up_arrow.png"
            elif direction == Direction.LEFT:
                icon_name = "left_arrow.png"
            elif direction == Direction.RIGHT:
                icon_name = "right_arrow.png"

            self.setPixmap(QPixmap("res/" + icon_name))

            self.setStyleSheet("border: none")

    def __init__(self):
        super().__init__()
        self.instructions: list[SemiDriveInstruction] = []

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        # Draw all current instructions in list
        self.draw_instructions()

        # Update gui when instructions are created or deleted
        backend_signals().new_semi_instruction.connect(self.add_instruction)
        backend_signals().remove_semi_instruction.connect(self.remove_instruction)
        backend_signals().clear_semi_instructions.connect(self.clear_all)

        self.setStyleSheet("border: 1px solid grey")

    def draw_instructions(self):
        queue = QWidget()
        queue.setStyleSheet("border: none")
        self.setWidget(queue)

        layout = QHBoxLayout(queue)
        layout.setSpacing(15)

        for instruction in self.instructions:
            layout.addWidget(self.InstructionWidget(instruction.direction))

        layout.addStretch()  # Left align padding

    def add_instruction(self, instruction: SemiDriveInstruction):
        """ Adds instruction to plan """
        self.instructions.append(instruction)

        layout = self.widget().layout()
        # Add instruction to end, but before the padding
        layout.insertWidget(
            layout.count()-1, self.InstructionWidget(instruction.direction))

    def remove_instruction(self, id: str):
        """ Removes instruction, if it exists """
        list_len = len(self.instructions)

        # Remove instruction with given id
        self.instructions = [ins for ins in self.instructions if ins.id != id]

        if len(self.instructions) == list_len:
            # No intruction with the id existed
            LOG("ERROR", "Instruction with id \"{}\" not found".format(id))
            return

        print("Completed semi-auto drive instruction", id)
        self.draw_instructions()  # Redraw queue

    def clear_all(self):
        """ Remove all instructions and reset widget """
        self.instructions = []
        print("Queue cleared")
        self.draw_instructions()  # Redraw queue


class AutoPlanWidget(QScrollArea):
    """ A box that lists the current drive mission """

    class DestinationLabel(QLabel):
        """ Small label showing a destination name """

        def __init__(self, dest_name: str):
            super().__init__()
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self.setMaximumHeight(90)

            font = self.font()
            font.setPointSize(30)
            self.setFont(font)
            self.setText(dest_name)

            self.setStyleSheet("border: 1px solid grey")

    def __init__(self):
        super().__init__()
        self.mission = DriveMission()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        # Draw all current instructions in list
        self.draw_mission()

        # Update gui plan when current drive mission is updated
        backend_signals().update_drive_mission.connect(self.update_mission)

        self.setStyleSheet("border: 1px solid grey")

    def draw_mission(self):
        queue = QWidget()
        queue.setStyleSheet("border: none")
        self.setWidget(queue)

        layout = QHBoxLayout(queue)
        layout.setSpacing(15)

        for dest in self.mission.destinations:
            layout.addWidget(self.DestinationLabel(dest))

        layout.addStretch()  # Left align padding

    def update_mission(self, mission: DriveMission):
        """ Updates mission in plan """
        self.mission = mission
        self.draw_mission()


class LogWidget(QTabWidget):
    """ A log that displays log data from backend """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.logger = QPlainTextEdit(self)
        self.logger.setReadOnly(True)
        self.text = ""
        backend_signals().log_msg.connect(self.add_log)  # Add a log from backend

        self.addTab(self.logger, "Logg")

    def add_log(self, severity, message):
        """ Adds message with severity and timestamp to the log widget on GUI """
        current_time = \
            str(localtime().tm_hour).zfill(2) + ":" + \
            str(localtime().tm_min).zfill(2) + ":" + \
            str(localtime().tm_sec).zfill(2)

        entry = "[" + current_time + " - " + severity + "]\t" + message
        self.logger.appendPlainText(entry)


class ParameterWidget(QWidget):
    """ A popup widget where parameters can be configured """

    def __init__(self):
        super().__init__()

        layout = QFormLayout(self)
        layout.setSpacing(10)

        # Add fields for each parameter
        self.steer_kp_textbox = QLineEdit()
        self.steer_kd_textbox = QLineEdit()
        self.speed_kp_textbox = QLineEdit()
        self.speed_ki_textbox = QLineEdit()
        self.angle_offset_textbox = QLineEdit()
        self.turn_kd_textbox = QLineEdit()
        layout.addRow(QLabel("STEER_KP"), self.steer_kp_textbox)
        layout.addRow(QLabel("STEER_KD"), self.steer_kd_textbox)
        layout.addRow(QLabel("SPEED_KP"), self.speed_kp_textbox)
        layout.addRow(QLabel("SPEED_KI"), self.speed_ki_textbox)
        layout.addRow(QLabel("TURN_KD"), self.turn_kd_textbox)
        layout.addRow(QLabel("ANGLE_OFFSET"), self.angle_offset_textbox)

        btn_layout = QHBoxLayout()

        # Send and close buttons
        send_btn = QPushButton("Skicka")
        send_btn.clicked.connect(self.send_params)
        cancel_btn = QPushButton("Stäng")
        cancel_btn.clicked.connect(self.close_popup)

        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def send_params(self):
        """ Send entered paramters to car """
        LOG("INFO", "Sending new parameters to car")

        # Save entered params in object
        self.params.steering_kp = int(self.steer_kp_textbox.text())
        self.params.steering_kd = int(self.steer_kd_textbox.text())
        self.params.speed_kp = int(self.speed_kp_textbox.text())
        self.params.speed_ki = int(self.speed_ki_textbox.text())
        self.params.turn_kd = int(self.turn_kd_textbox.text())
        self.params.angle_offset = int(self.angle_offset_textbox.text())

        socket().send_message(self.params.to_json())
        self.close_popup()

    def close_popup(self):
        """ Close popup """
        self.close()

    def open_popup(self, params=ParameterConfiguration()):
        """ Open parmater configuration dialogbox, provide current params instance """
        self.params = params  # Update params

        # Autofill text boxes with current params
        self.steer_kp_textbox.setText(str(self.params.steering_kp))
        self.steer_kd_textbox.setText(str(self.params.steering_kd))
        self.speed_kp_textbox.setText(str(self.params.speed_kp))
        self.speed_ki_textbox.setText(str(self.params.speed_ki))
        self.turn_kd_textbox.setText(str(self.params.turn_kd))
        self.angle_offset_textbox.setText(str(self.params.angle_offset))

        self.setMinimumSize(300, 60)
        self.setWindowTitle("Parameterkonfiguration")
        self.show()


class ControlsWidget(QWidget):
    """ A controls area where the user can control the car. Has different modes. """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QHBoxLayout(self)
        layout_l = QVBoxLayout()

        # Initate parameters with default values
        self.param_data = ParameterConfiguration(STEER_KP, STEER_KD,
                                                 SPEED_KP, SPEED_KI,
                                                 TURN_KD, ANGLE_OFFSET)
        param = ParameterWidget()

        # Parameter button
        param_btn = QPushButton("Parametrar")
        param_btn.setFixedSize(125, 60)
        param_btn.clicked.connect(lambda: param.open_popup(self.param_data))
        layout_l.addWidget(param_btn)

        # Emergency stop button
        stop_btn = QPushButton('STOP')
        stop_btn.setFixedSize(125, 125)
        stop_btn.setStyleSheet(
            "background-color: red; border : 2px solid darkred;font-size: 20px;font-family: Arial")
        stop_btn.clicked.connect(socket().emergency_stop_car)
        layout_l.addWidget(stop_btn)

        # Add stop and param buttons stacked on the left
        layout.addLayout(layout_l)

        self.controls = QStackedWidget()
        self.controls.setStyleSheet("border: none")

        manual_mode = ManualMode()
        semi_mode = SemiMode()
        auto_mode = AutoMode()

        self.controls.insertWidget(DrivingMode.MANUAL, manual_mode)
        self.controls.insertWidget(DrivingMode.SEMIAUTO, semi_mode)
        self.controls.insertWidget(DrivingMode.AUTO, auto_mode)

        backend_signals().change_drive_mode.connect(self.switch_mode)

        # Add controls on the right
        layout.addWidget(self.controls)

        self.setStyleSheet("border: 1px solid grey")

    def switch_mode(self, mode: DrivingMode):
        """ Change which controls are currently visible """
        self.controls.setCurrentIndex(mode)


class ManualMode(QWidget):
    """ The buttons needed for manual driving """

    class DriveButton(QToolButton):
        """ A button for steering the car in manual mode"""

        def __init__(self, action, arrow):
            super().__init__()

            size_policy = QSizePolicy()
            size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
            size_policy.setVerticalPolicy(QSizePolicy.Expanding)
            size_policy.setWidthForHeight(True)  # Ensure square button

            self.clicked.connect(action)
            self.setAutoRepeat(True)
            self.setAutoRepeatInterval(MAX_SEND_RATE * 250)
            self.setArrowType(arrow)
            self.setSizePolicy(size_policy)
            self.setStyleSheet("border: 1px solid grey")

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.create_drive_buttons()
        self.setup_keyboard_shortcuts()

        self.timer = time()

    def create_drive_buttons(self):
        """ Adds drive buttons in a 3x2 grid """
        layout = QGridLayout(self)

        fwrd = self.DriveButton(self.send_fwrd, Qt.UpArrow)
        layout.addWidget(fwrd, 0, 1)

        bwrd = self.DriveButton(self.send_bwrd, Qt.DownArrow)
        layout.addWidget(bwrd, 1, 1)

        left = self.DriveButton(self.send_left, Qt.LeftArrow)
        layout.addWidget(left, 1, 0)

        right = self.DriveButton(self.send_right, Qt.RightArrow)
        layout.addWidget(right, 1, 2)

        fwrd_right = self.DriveButton(self.send_fwrd_right, Qt.NoArrow)
        layout.addWidget(fwrd_right, 0, 2)

        fwrd_left = self.DriveButton(self.send_fwrd_left, Qt.NoArrow)
        layout.addWidget(fwrd_left, 0, 0)

        self.setLayout(layout)

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
        self.send_drive_instruction(ManualDriveInstruction(CAR_ACC, 0))

    def send_bwrd(self):
        self.send_drive_instruction(ManualDriveInstruction(0, 0))

    def send_right(self):
        self.send_drive_instruction(
            ManualDriveInstruction(CAR_ACC, FULL_STEER))

    def send_left(self):
        self.send_drive_instruction(
            ManualDriveInstruction(CAR_ACC, -FULL_STEER))

    def send_fwrd_right(self):
        self.send_drive_instruction(
            ManualDriveInstruction(CAR_ACC, HALF_STEER))

    def send_fwrd_left(self):
        self.send_drive_instruction(
            ManualDriveInstruction(CAR_ACC, -HALF_STEER))

    def send_drive_instruction(self, drive_instruction: ManualDriveInstruction):
        """ Sends drive intruction at approximately MAX_SEND_RATE (Hz) """
        new_time = time()
        if new_time - self.timer > MAX_SEND_RATE:
            socket().send_message(drive_instruction.to_json())
            self.timer = new_time  # Reset timer


class SemiMode(QWidget):
    """ Buttons needed to drive the car in semi-autonomous mode """

    class DriveButton(QPushButton):
        """ A button for steering the car in semi-autonomous mode  """
        size_policy = QSizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)

        def __init__(self, action, icon_path):
            super().__init__()
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(90, 120))  # Set size to image size
            self.clicked.connect(action)
            self.setSizePolicy(self.size_policy)
            self.setStyleSheet("border: 1px solid grey")

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)

        left_btn = self.DriveButton(self.send_left, "res/left_arrow.png")
        fwrd_btn = self.DriveButton(self.send_fwrd, "res/up_arrow.png")
        right_btn = self.DriveButton(self.send_right, "res/right_arrow.png")

        layout.addWidget(left_btn)
        layout.addWidget(fwrd_btn)
        layout.addWidget(right_btn)

    def send_left(self):
        self.send(SemiDriveInstruction(Direction.LEFT))

    def send_fwrd(self):
        self.send(SemiDriveInstruction(Direction.FWRD))

    def send_right(self):
        self.send(SemiDriveInstruction(Direction.RIGHT))

    def send(self, instruction):
        """ Send instruction to car and plan widget """
        socket().send_message(instruction.to_json())
        backend_signals().new_semi_instruction.emit(instruction)


class AutoMode(QWidget):
    """ Controls needed to drive the car in fully autonomous mode """

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setStyleSheet("border: 1px solid grey")

        layout = QHBoxLayout(self)

        # Input area
        self.destination_input = QPlainTextEdit()
        self.destination_input.setPlaceholderText("Destination")
        font = self.destination_input.font()
        font.setPointSize(25)
        self.destination_input.setFont(font)
        layout.addWidget(self.destination_input)

        # Buttons
        btn_layout = QVBoxLayout()
        self.create_buttons(btn_layout)
        layout.addLayout(btn_layout)

        self.auto = DriveMission()

    def create_buttons(self, btn_layout: QVBoxLayout):
        """ Creates buttons for modifying drive mission """
        # Add destination button
        add_btn = QPushButton("Add")
        add_btn.setFixedSize(100, 50)
        add_btn.clicked.connect(self.add_destination)
        btn_layout.addWidget(add_btn)

        # Clear mission button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(100, 50)
        clear_btn.clicked.connect(self.clear_mission)
        btn_layout.addWidget(clear_btn)

        # Start mission button
        start_btn = QPushButton("Start")
        start_btn.setFixedSize(100, 50)
        start_btn.clicked.connect(self.send_mission)
        btn_layout.addWidget(start_btn)

    def clear_mission(self):
        """ Deletes all destinations from mission """
        self.auto.clear()
        self.destination_input.setPlainText("")  # Clear input space
        backend_signals().update_drive_mission.emit(self.auto)

    def add_destination(self):
        """ Adds a new destination to the current drive mission """
        new_dest = self.destination_input.toPlainText().strip()  # Get input

        if new_dest == "":
            LOG("ERROR", "Can't add empty node")
            return
        elif [new_dest] == self.auto.destinations[-1:]:
            # New destination is same as last
            LOG("ERROR", "Can't drive to self, destination " + new_dest)
            return

        print("Adding new destination", new_dest)

        self.auto.add_destination(new_dest)
        self.destination_input.setPlainText("")  # Clear input space
        backend_signals().update_drive_mission.emit(self.auto)
        print(self.auto.to_json())

    def send_mission(self):
        """ Send current drive mission to car """
        LOG("INFO", "Sending driving mission")
        socket().send_message(self.auto.to_json())


class ButtonsWidget(QWidget):
    """ Buttons that can change which drivning mode is used to control the car """

    class ModeButton(QPushButton):
        """ A button that can toggle driving modes for the application """

        def __init__(self, label: str, mode: DrivingMode):
            super().__init__()
            self.setMinimumSize(110, 45)

            self.setText(label)
            self.clicked.connect(lambda: self.switch_mode(mode))

        def switch_mode(self, mode: DrivingMode):
            """ Signals to app to switch driving mode """
            backend_signals().change_drive_mode.emit(mode)

    def __init__(self, change_mode=lambda: None):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)

        manual_btn = self.ModeButton("Manuell", DrivingMode.MANUAL)
        semi_btn = self.ModeButton("Semiautonom", DrivingMode.SEMIAUTO)
        full_btn = self.ModeButton("Helautonom", DrivingMode.AUTO)

        layout.addWidget(manual_btn)
        layout.addWidget(semi_btn)
        layout.addWidget(full_btn)
