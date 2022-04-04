from PySide6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QPushButton, QSizePolicy, QStackedWidget,
                               QTableWidget, QTabWidget, QVBoxLayout, QWidget)


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

        layout = QVBoxLayout(self)
        layout.addWidget(param_btn)
        layout.addWidget(stop_btn)


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
