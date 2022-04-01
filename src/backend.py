from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtWebSockets import QWebSocket, QWebSocketProtocol
from PySide6.QtWidgets import QApplication

# Based on:
#
# https://stackoverflow.com/questions/35237245/how-to-create-a-websocket-client-by-using-qwebsocket-in-pyqt5

PORT = "8000"
URL = "ws://localhost:" + PORT


class WebSocket(QObject):
    """A websocket for communication with the car"""

    def __init__(self, parent):
        super().__init__(parent)

        self.client = QWebSocket(
            "", QWebSocketProtocol.Version13, self)
        self.client.error.connect(self.error)

        print("Connecting to server [{}]".format(URL))
        self.client.open(QUrl(URL))

        self.client.pong.connect(self.on_pong)

    def ping(self):
        print("Sending ping to server...")
        try:
            self.client.ping(b"PING")
        except Exception as e:
            print("ERROR: ", str(e))

    def on_pong(self, elapsedTime, payload):
        print("Pong received [time: {} ; payload: {}]".format(
            elapsedTime, str(payload)))

    def send_message(self, message: str):
        '''Sends message to server'''
        print("Sending: ", message)
        try:
            self.client.sendTextMessage(message)
        except Exception as e:
            print("ERROR: ", str(e))
        finally:
            self.close("Finished")  # Close after message sent

    def error(self, error_code):
        print("ERROR CODE:", error_code)
        print("ERROR MESSAGE:", self.client.errorString())

    def close(self, reason: str = "unspecified"):
        print("Closing websocket [Reason {}]".format(reason))
        self.client.close(QWebSocketProtocol.CloseCodeNormal, reason)


# Test scripts
def send_message(client: WebSocket, msg: str):
    client.send_message(msg)


def ping(client: WebSocket):
    client.ping()


if __name__ == '__main__':
    app = QApplication([])
    client = WebSocket(app)

    QTimer.singleShot(2000, lambda: ping(client))
    QTimer.singleShot(3000, lambda: send_message(client, "YO!"))
    QTimer.singleShot(10000, app.exit)

    app.exec()
