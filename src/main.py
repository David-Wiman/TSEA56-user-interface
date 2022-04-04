from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenu,
                               QVBoxLayout, QWidget, QWidgetAction)

from graphics_widgets import (ButtonsWidget, ControlsWidget, DataWidget,
                              LogWidget, MapWidget, PlanWidget)

GUI_WIDTH = 1280
GUI_HEIGHT = 720


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

    def create_menu(self):
        menu_bar = self.menuBar()

        file_menu = QMenu("File")
        file_action = QWidgetAction(file_menu)
        file_menu.addAction(file_action)
        menu_bar.addMenu(file_menu)

        settings_menu = QMenu("Settings")
        settings_action = QWidgetAction(file_menu)
        settings_menu.addAction(settings_action)
        menu_bar.addMenu(settings_menu)

        map_menu = QMenu("Map")
        map_action = QWidgetAction(file_menu)
        map_menu.addAction(map_action)
        menu_bar.addMenu(map_menu)

    def create_grid(self):
        layout_hori = QHBoxLayout()
        layout_vert_l = QVBoxLayout()
        layout_vert_r = QVBoxLayout()

        map_widget = MapWidget()
        data_widget = DataWidget()
        plan_widget = PlanWidget()
        logg_widget = LogWidget()
        controls_widget = ControlsWidget()
        buttons_widget = ButtonsWidget(
            lambda mode: controls_widget.set_index(mode))

        layout_vert_l_top = QHBoxLayout()
        layout_vert_l_top.addWidget(map_widget)
        layout_vert_l_top.addWidget(data_widget)
        layout_vert_l.addLayout(layout_vert_l_top, 65)
        layout_vert_l.addWidget(logg_widget, 35)
        layout_hori.addLayout(layout_vert_l, 60)

        layout_vert_r.addWidget(plan_widget)
        layout_vert_r.addWidget(buttons_widget)
        layout_vert_r.addWidget(controls_widget)
        layout_hori.addLayout(layout_vert_r, 40)

        self.central_widget.setLayout(layout_hori)


if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
