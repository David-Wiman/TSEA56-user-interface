from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenu,
                               QVBoxLayout, QWidget)

from backend import backend_signals, socket
from config import GUI_HEIGHT, GUI_WIDTH
from graphics_widgets import (ButtonsWidget, ControlsWidget, DataWidget,
                              LogWidget, MapWidget, PlanWidget)
from map_creator import MapCreatorWindow


class MainWindow(QMainWindow):
    """Main window for the application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo")
        self.setGeometry(0, 0, GUI_WIDTH, GUI_HEIGHT)
        self.setMinimumSize(GUI_WIDTH, GUI_HEIGHT)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.create_menu()
        self.create_grid()

        socket()  # Init socket

    def create_menu(self):
        menu_bar = self.menuBar()

        file_menu = QMenu("File", menu_bar)
        connect_action = QAction("Connect to car", file_menu)
        connect_action.triggered.connect(self.connect_to_car)
        file_menu.addAction(connect_action)
        clear_action = QAction("Clear plan", file_menu)
        clear_action.triggered.connect(self.clear_instructions)
        file_menu.addAction(clear_action)
        menu_bar.addMenu(file_menu)

        map_menu = QMenu("Map", menu_bar)
        edit_map_action = QAction("Edit map", map_menu)
        edit_map_action.triggered.connect(self.open_map_editor)
        map_menu.addAction(edit_map_action)
        map_send = QAction("Send map to car", map_menu)
        map_send.triggered.connect(self.send_map)
        map_menu.addAction(map_send)
        menu_bar.addMenu(map_menu)

    def create_grid(self):
        layout_hori = QHBoxLayout()
        layout_vert_l = QVBoxLayout()
        layout_vert_r = QVBoxLayout()

        self.map_widget = MapWidget()
        data_widget = DataWidget()
        plan_widget = PlanWidget()
        logg_widget = LogWidget()
        controls_widget = ControlsWidget()
        buttons_widget = ButtonsWidget()

        layout_vert_l_top = QHBoxLayout()
        layout_vert_l_top.addWidget(self.map_widget)
        layout_vert_l_top.addWidget(data_widget)
        layout_vert_l.addLayout(layout_vert_l_top, 65)
        layout_vert_l.addWidget(logg_widget, 35)
        layout_hori.addLayout(layout_vert_l, 60)

        layout_vert_r.addWidget(plan_widget)
        layout_vert_r.addWidget(buttons_widget)
        layout_vert_r.addWidget(controls_widget)
        layout_hori.addLayout(layout_vert_r, 40)

        self.central_widget.setLayout(layout_hori)

    def open_map_editor(self):
        self.map_creator = MapCreatorWindow()
        self.map_creator.show()

    def connect_to_car(self):
        socket().connect()

    def clear_instructions(self):
        backend_signals().clear_semi_instructions.emit()

    def send_map(self):
        """ Sends current map instance to car """
        map: str
        with open("map/map.json", "r") as file:
            map = file.read().rstrip().replace("\n", "").replace("  ", "")
        backend_signals().log_msg.emit("INFO", "Sending map to car")
        socket().send_message(map)


if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
