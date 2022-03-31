from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu,
                               QWidget, QWidgetAction)

from graphics_widgets import (ButtonsWidget, ControlsWidget, DataWidget,
                              LogWidget, MapWidget, PlanWidget)

GUI_WIDTH = 1280
GUI_HEIGHT = 720


class MainWindow(QMainWindow):
    """Main window for the application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo")
        self.setFixedSize(GUI_WIDTH, GUI_HEIGHT)

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
        # 32x18
        grid_layout = QGridLayout(self.central_widget)

        map_widget = MapWidget()
        data_widget = DataWidget()
        plan_widget = PlanWidget()
        logg_widget = LogWidget()
        controls_widget = ControlsWidget()
        buttons_widget = ButtonsWidget(
            lambda mode: controls_widget.set_index(mode))

        # [QWidget], row, col, row_span, col_span
        grid_layout.addWidget(map_widget, 0, 0, 12, 12)
        grid_layout.addWidget(data_widget, 0, 12, 12, 8)
        grid_layout.addWidget(logg_widget, 12, 0, 6, 20)

        grid_layout.addWidget(plan_widget, 0, 20, 8, 12)
        grid_layout.addWidget(buttons_widget, 8, 20, 3, 12)
        grid_layout.addWidget(controls_widget, 11, 20, 7, 12)


if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
