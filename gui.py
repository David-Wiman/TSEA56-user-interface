#!/usr/bin/python
from http import client
from opcode import hasname
import sys
from PyQt5 import QtCore, QtWebSockets, QtNetwork
from PyQt5.QtWidgets import  (QWidget, QLabel, QApplication, QPushButton, QListWidget, 
                            QProgressBar, QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
                            QVBoxLayout, QMainWindow, QAbstractItemView, QLineEdit, QShortcut, QMessageBox)
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot, QObject, QUrl, QCoreApplication, QTimer
from PyQt5.QtGui import QImage, QPixmap, QKeySequence, QDoubleValidator

from math import *
import websocket

##################################################################

class GUI(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()

        self.thread = ListenWebsocket()
        self.thread.start()
        self.initUI()

##-----------------------------------------------------------------------------------------------------------

    def initUI(self):
        #create mainwindow
        self.setWindowTitle("Taxibil GUI")
        self.setGeometry(250, 100, 1100, 687)

        #create a Image Label
        self.imageLabel = QLabel(self)
        self.imageLabel.move(4, 4)
        self.imageLabel.resize(640, 480)
        #create QTableWidget for logger
        self.logger =QTableWidget(self)
        self.logger.resize(780,180)
        self.logger.setRowCount(6)
        self.logger.setColumnCount(4)
        self.logger.setColumnWidth(0, 400)
        self.logger.setColumnWidth(1, 80)
        self.logger.setColumnWidth(2, 158)
        self.logger.setHorizontalHeaderLabels(("Message;Severity;Node;Timestamp").split(";"))

        #creating tabWidget to insert logger osv
        self.tabWidget = QTabWidget(self)
        self.tabWidget.move(10, 440)
        self.tabWidget.resize(580,240)
        self.tabWidget.addTab(self.logger, "Logg")
    

        """Desiding driving mode"""
        # create push button - Helautonom
        self.helAuto_btn = QPushButton("Helautonom", self)
        self.helAuto_btn.move(665, 390)
        self.helAuto_btn.resize(110, 45)
        self.helAuto_btn.clicked.connect(lambda:choose_mode("Helautonom"))

        # create push button - Halvautonom
        self.halvAuto_btn = QPushButton("Halvautonom", self)
        self.halvAuto_btn.move(795, 390)
        self.halvAuto_btn.resize(110, 45)
        self.halvAuto_btn.clicked.connect(lambda:choose_mode("Halvautonom"))

        # create push button - Manuell
        self.manuell_btn = QPushButton("Manuell", self)
        self.manuell_btn.move(925, 390)
        self.manuell_btn.resize(110, 45)
        self.manuell_btn.clicked.connect(lambda:choose_mode("Manuell"))

        """ CONTROLLER """
        #creating edge for controller
        self.controllerEdge = QLabel(self)
        self.controllerEdge.setStyleSheet("border: 1px solid grey")
        self.controllerEdge.move(650, 440)
        self.controllerEdge.resize(445, 240)

        # create push button - parameter
        self.param_btn = QPushButton("Parametrar", self)
        self.param_btn.move(665, 460)
        self.param_btn.resize(110, 60)

        #create push button - stop
        self.stop_btn = QPushButton('STOP', self)
        self.stop_btn.move(665, 540)
        self.stop_btn.resize(70,70)
        self.stop_btn.setStyleSheet("background-color: red; border : 2px solid darkred;font-size: 20px;font-family: Arial")
        self.stop_btn.clicked.connect(client.send_stop_msg)

        """Path planner"""
        #creating edge - path planner
        self.edgeLabel = QLabel(self)
        self.edgeLabel.setStyleSheet("border: 1px solid grey")
        self.edgeLabel.move(650, 65)
        self.edgeLabel.resize(445, 300)

        # create push button - A
        self.a_btn = QPushButton("A", self)
        self.a_btn.move(665, 100)
        self.a_btn.resize(70, 70)
        self.a_btn.clicked.connect(lambda:path_func("A"))

        # create push button - B
        self.b_btn = QPushButton("B", self)
        self.b_btn.move(765, 100)
        self.b_btn.resize(70, 70)
        self.b_btn.clicked.connect(lambda:path_func("B"))

        # create push button - C
        self.c_btn = QPushButton("C", self)
        self.c_btn.move(865, 100)
        self.c_btn.resize(70, 70)
        self.c_btn.clicked.connect(lambda:path_func("C"))

        # create push button - D
        self.d_btn = QPushButton("D", self)
        self.d_btn.move(665, 200)
        self.d_btn.resize(70, 70)
        self.d_btn.clicked.connect(lambda:path_func("D"))

        # create push button - E
        self.e_btn = QPushButton("E", self)
        self.e_btn.move(765, 200)
        self.e_btn.resize(70, 70)
        self.e_btn.clicked.connect(lambda:path_func("E"))

        # create push button - F
        self.f_btn = QPushButton("F", self)
        self.f_btn.move(865, 200)
        self.f_btn.resize(70, 70)
        self.f_btn.clicked.connect(lambda:path_func("F"))

        # create label - path
        self.path_lbl = QLabel(self)
        self.path_lbl.move(665, 260)
        self.path_lbl.resize(70,50)
        self.path_lbl.setText("Körplan")

        # Create textbox - path
        self.path_box = QLineEdit(self)
        self.path_box.move(665, 300)
        self.path_box.resize(180,40)

        """" Data """
        #creating edge - data
        self.edgeLabel = QLabel(self)
        self.edgeLabel.setStyleSheet("border: 1px solid grey")
        self.edgeLabel.move(390, 35)
        self.edgeLabel.resize(240, 350)

        # create label - Data
        self.data_lbl = QLabel(self)
        self.data_lbl.move(400, 45)
        self.data_lbl.resize(70,50)
        self.data_lbl.setText("Data")

        # create label - Drive Time
        self.drive_time_lbl = QLabel(self)
        self.drive_time_lbl.move(400, 85)
        self.drive_time_lbl.resize(90,50)
        self.drive_time_lbl.setText("Körtid:")

        # create label - Gas
        self.gas_lbl = QLabel(self)
        self.gas_lbl.move(400, 125)
        self.gas_lbl.resize(90,50)
        self.gas_lbl.setText("Gaspådrag:")

        # create label - Strearing
        self.stear_lbl = QLabel(self)
        self.stear_lbl.move(400, 165)
        self.stear_lbl.resize(90,50)
        self.stear_lbl.setText("Styrutslag:")

        # create label - Velocity
        self.vel_lbl = QLabel(self)
        self.vel_lbl.move(400, 205)
        self.vel_lbl.resize(90,50)
        self.vel_lbl.setText("Hastighet:")

        # create label - Distance
        self.dist_lbl = QLabel(self)
        self.dist_lbl.move(400, 245)
        self.dist_lbl.resize(90,50)
        self.dist_lbl.setText("Körsträcka:")

        # create label - lateral dist
        self.lat_lbl = QLabel(self)
        self.lat_lbl.move(400, 285)
        self.lat_lbl.resize(90,50)
        self.lat_lbl.setText("Lateral:")
        
        self.show() #Displaying GUI

        """ Creating different keybord shortcuts"""
        self.shortcut_fwrd = QShortcut(QKeySequence("w"), self)
        self.shortcut_fwrd.activated.connect(client.send_fwrd_msg)

        self.shortcut_bwrd = QShortcut(QKeySequence("s"), self)
        self.shortcut_bwrd.activated.connect(client.send_bwrd_msg)

        self.shortcut_bwrd = QShortcut(QKeySequence("d"), self)
        self.shortcut_bwrd.activated.connect(client.send_right_msg)

        self.shortcut_bwrd = QShortcut(QKeySequence("a"), self)
        self.shortcut_bwrd.activated.connect(client.send_left_msg)

""" Class for sending msg to server """
class Client(QtCore.QObject):
    def __init__(self, parent):
        
        super().__init__(parent)
        PORT = "8000"
        URL = "ws://localhost:" + PORT

        self.client =  QtWebSockets.QWebSocket("",QtWebSockets.QWebSocketProtocol.Version13,None)
        self.client.error.connect(self.error)

        self.client.open(QUrl(URL))
    

    def send_stop_msg(self):
        print("client: send_message")
        self.client.sendTextMessage("stop")

    def send_fwrd_msg(self):
        print("client: send_message")
        self.client.sendTextMessage("forward")

    def send_bwrd_msg(self):
        print("client: send_message")
        self.client.sendTextMessage("backward")

    def send_right_msg(self):
        print("client: send_message")
        self.client.sendTextMessage("right")

    def send_left_msg(self):
        print("client: send_message")
        self.client.sendTextMessage("left")

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.client.errorString())

""" Class for reading msg from server """
class ListenWebsocket(QtCore.QThread):
    def __init__(self, parent=None):
        super(ListenWebsocket, self).__init__(parent)

        websocket.enableTrace(True)

        self.WS = websocket.WebSocketApp("ws://localhost:8000",
                                on_message = self.on_message,
                                on_error = self.on_error)

    def run(self):
        #ws.on_open = on_open

        self.WS.run_forever()

    def on_message(self, ws, message):
        print (message)

    def on_error(self, ws, error):
        print (error)

""" Functing for printing path to GUI """
def path_func(str):
    path = gui.path_box.displayText()
    if str!="clear":
        gui.path_box.setText(path+" "+str)
    else:
        gui.path_box.setText("")
    
    
    print("go to ", str)

""" Function for choosing driving mode """
def choose_mode(str):
    print("Driving in: ", str)

##---------------------------------------------------------------------------------------------
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    client = Client(app)
    gui = GUI()

    app.exec_()

    