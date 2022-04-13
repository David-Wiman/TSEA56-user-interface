from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QApplication

from data import (CarData, ManualDriveInstruction, SemiDriveInstruction,
                  get_type_and_data)

PORT = 1234
URL = "192.168.1.31"


class BackendSignals(QObject):
    """ A singleton class, containing the signals needed to update UI """

    # Maintain only one instance
    _instance = None

    new_car_data = Signal(CarData)
    """ New car data has been recieved from the car"""

    log_msg = Signal(str, str)
    """ New severity and message has been sent to logger """

    new_semi_instruction = Signal(SemiDriveInstruction)
    """ New semi-auto instruction has been sent """

    remove_semi_instruction = Signal(str)
    """ Call to remove a semi-auto instruction, with provided id """

    clear_semi_instructions = Signal()
    """ Removes all semi-auto instructions for ui """


def backend_signals():
    """ Returns instance of the current BackendSignals """
    if BackendSignals._instance is None:
        BackendSignals._instance = BackendSignals(QApplication.instance())
    return BackendSignals._instance


class Socket(QObject):
    """ A singleton class, representing a tcp socket for communication with the car """

    # Maintain only one websocket instance
    _instance = None

    def __init__(self, parent):
        super().__init__(parent)
        self.pSocket = QTcpSocket(self)
        self.pSocket.readyRead.connect(self.on_recieved)
        self.pSocket.connected.connect(self.on_connected)
        self.pSocket.disconnected.connect(self.on_disconnected)
        self.pSocket.errorOccurred.connect(self.on_error)

    def connect(self):
        """ Connect socket to host """
        self.log("Connecting to server....")
        self.pSocket.connectToHost(URL, PORT)

    def disconnect(self):
        """ Disconnect socket from host """
        self.log("Disconnecting from server...")
        self.pSocket.disconnectFromHost()

    def hard_stop_car(self):
        """ Sends emergency stop signal to car """
        self.log("EMERGENCY STOP", "WARN")
        self.send_message("STOP")

    def send_message(self, message: str):
        """ Sends message to server. Throws if connection not valid. """
        if (not self.pSocket.state() == QAbstractSocket.ConnectedState):
            self.log("No connection to server", "ERROR")
            print("Error sending:\n", message)
            raise ConnectionError("Socket not Connected")

        message += "\n"  # Add terminating char
        bytes = message.encode("utf-8")
        print("Sending:", bytes)
        self.pSocket.write(bytes)
        self.pSocket.flush()  # Clear buffer after send

    def on_recieved(self):
        bytes = self.pSocket.readAll()
        print("Reading data:", bytes)
        message = str(bytes)
        type, data = get_type_and_data(message)

        if type == "CarData":
            backend_signals().new_car_data.emit(CarData.from_json(data))
        else:
            print("Unknown type: " + type, "\n"+str(data))

    def on_error(self, error):
        print(error)
        if error == QAbstractSocket.ConnectionRefusedError:
            self.log('Unable to send data to port: "{}"'.format(PORT), "ERROR")
            self.log("trying to reconnect", "ERROR")
            QTimer.singleShot(1000, self.slotSendMessage)

    def on_connected(self):
        self.log("Connected")

    def on_disconnected(self):
        self.log("Disconnected")

    def log(self, message, severity="INFO"):
        backend_signals().log_msg.emit(severity, message)


def socket():
    """ Returns instance of the current tcp socket """
    if Socket._instance is None:
        Socket._instance = Socket(QApplication.instance())
    return Socket._instance


def send_message(socket: Socket):
    # test method
    socket.connect()
    successful = socket.pSocket.waitForConnected(1000)
    if not successful:
        print("Connection failed")

    socket.send_message(
        ManualDriveInstruction(throttle=10.0).to_json())

    QTimer.singleShot(1500, socket.disconnect())


if __name__ == '__main__':
    app = QApplication([])
    client = Socket(app)

    QTimer.singleShot(1100, lambda: send_message(client))
    QTimer.singleShot(10000, app.exit)

    app.exec()
