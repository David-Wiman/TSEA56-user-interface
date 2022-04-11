from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QApplication

from data import CarData, ManualDriveInstruction, get_type_and_data

PORT = 1234
URL = "192.168.1.31"


class BackendSignals(QObject):
    """ A singleton class, containing the signals from the backend needed to update UI """

    # Maintain only one instance
    _instance = None

    new_car_data = Signal(CarData)  # New car data has been recieved


def backend_signals():
    """ Returns instance of the current backend signals """
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
        print("Connecting to server....")
        self.pSocket.connectToHost(URL, PORT)

    def disconnect(self):
        """ Disconnect socket from host """
        print("Disconnecting from server...")
        self.pSocket.disconnectFromHost()

    def hard_stop_car(self):
        """ Sends emergency stop signal to car """
        self.send_message("STOP")

    def send_message(self, message: str):
        """ Sends message to server. Throws if connection not valid. """
        if (not self.pSocket.state() == QAbstractSocket.ConnectedState):
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
        if error == QAbstractSocket.ConnectionRefusedError:
            print('Unable to send data to port: "{}"'.format(PORT))
            print("trying to reconnect")
            QTimer.singleShot(1000, self.slotSendMessage)

    def on_connected(self):
        print("Connected")

    def on_disconnected(self):
        print("Disconnected")


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
    #QTimer.singleShot(2000, lambda: ping(client))
    #QTimer.singleShot(3000, lambda: send_message(client, "YO!"))
    #QTimer.singleShot(5000, lambda: close)
    QTimer.singleShot(10000, app.exit)

    app.exec()
