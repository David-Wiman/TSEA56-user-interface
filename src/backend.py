from PySide6.QtWebSockets import QWebSocket, QWebSocketProtocol
from PySide6.QtCore import QObject, QUrl, QTimer
from PySide6.QtWidgets import QApplication

URL = "ws://localhost"
PORT = "8000"


class WebSocket(QObject):
    """A websocket for communication with the car"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.client = QWebSocket("",QWebSocketProtocol.Version13,None)
        self.client.error.connect(self.error)

        self.client.open(QUrl(URL + ":" + PORT))
        self.client.pong.connect(self.onPong)

    def do_ping(self):
        print("client: do_ping")
        self.client.ping(b"foo")

    def send_message(self):
        print("client: send_message")
        self.client.sendTextMessage("asd")

    def onPong(self, elapsedTime, payload):
        print("onPong - time: {} ; payload: {}".format(elapsedTime, payload))

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.client.errorString())

    def close(self):
        self.client.close()


# Testkod nedan
if __name__ == '__main__':
    global client
    app = QApplication([])
    client = WebSocket(app)

    QTimer.singleShot(2000, client.do_ping)
    QTimer.singleShot(3000, client.send_message)
    QTimer.singleShot(5000, client.close)

    app.exec()
