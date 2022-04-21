# This file contains configuration constants

# Screen size
GUI_WIDTH = 1280
GUI_HEIGHT = 720

# File paths
DATA_PATH = "data/"
""" Path to folder where the csv-files will be saved """

# Backend configuration
PORT = 1234
""" Port the socket will try to connect to """

SERVER_IP = "192.168.1.31"
""" IP-address to the server """

# Manual mode constants
CAR_ACC = 100
""" Throttle sent when driving """

FULL_STEER = 280
""" Steer angle sent when user presses turn key """

HALF_STEER = 100
""" Steer angle sent when user presses diagonal turn key """

MAX_SEND_RATE = 1/10
""" Max rate at which manual instructions will be sent """

# Default regulation control paramters
STEER_KP = 1
""" Default value for steering kp """

STEER_KD = 0
""" Default value for steering kd """

SPEED_KP = 1
""" Default value for speed kp """

SPEED_KI = 0
""" Default value for steering ki """