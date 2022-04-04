from time import sleep

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWebSockets import QWebSocket, QWebSocketProtocol
from PySide6.QtWidgets import QApplication

from data import get_type_and_data

# Based on:
#
# https://stackoverflow.com/questions/35237245/how-to-create-a-websocket-client-by-using-qwebsocket-in-pyqt5

PORT = "8000"
URL = "ws://localhost:" + PORT


class WebSocket(QObject):
    """A websocket for communication with the car"""

    def __init__(self, parent):
        super().__init__(parent)
        print("Connecting to server [{}]".format(URL))
        self.client = QWebSocket("", QWebSocketProtocol.Version13, self)
        self.client.open(QUrl(URL))

        self.client.connected.connect(self.on_connect)
        self.client.error.connect(self.error)
        self.client.pong.connect(self.on_pong)
        self.client.textMessageReceived.connect(self.on_message_recieve)
        self.client.disconnected.connect(self.on_disconnect)

    def ping(self):
        print("Sending ping to server...")
        self.client.ping(b"PING")

    def on_pong(self, elapsedTime, payload):
        print("Pong received [time: {} ; payload: {}]".format(
            elapsedTime, str(payload)))

    def send_message(self, message: str):
        '''Sends message to server'''
        if not self.client.isValid():
            # Verify that connection is ready to transmit
            raise Exception("Connection not valid!")

        print("Sending: ", message)
        self.client.sendTextMessage(message)
        # self.close("Finished")  # Close after message sent

    def on_message_recieve(self, message):
        print("Recieved: ", message)
        type, data = get_type_and_data(message)

        if type == "carData":
            print("Is car data!", data)
        else:
            print("Unknown type: " + type, "\n"+str(data))

    def error(self, error_code: QAbstractSocket.SocketError):
        print("ERROR: {} + ({})".format(self.client.errorString(), error_code.name))

    def on_connect(self):
        print("Connected to server.")

    def on_disconnect(self):
        print("Disconnected from server.")

    def close(self, reason: str = "unspecified", code=QWebSocketProtocol.CloseCodeNormal):
        print("Closing websocket [Reason {} ({})]".format(reason, code))
        self.client.close(code, reason)


# Test scripts
def send_message(client: WebSocket, msg: str):
    client.send_message(msg)


def ping(client: WebSocket):
    client.ping()


def close():
    client.close()


if __name__ == '__main__':
    app = QApplication([])
    client = WebSocket(app)

    QTimer.singleShot(2000, lambda: ping(client))
    QTimer.singleShot(3000, lambda: send_message(client, "YO!"))
    QTimer.singleShot(5000, lambda: close)
    QTimer.singleShot(10000, app.exit)

    app.exec()
