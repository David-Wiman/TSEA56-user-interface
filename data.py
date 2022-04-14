import json
from uuid import uuid4


class JSONSerializable:
    """ Enables a simple dataclass to be serialized with JSON """

    def to_json(self, type_name: str) -> str:
        """ Creates a JSON-object from instance, with the type as top level key """
        payload = json.dumps(self, default=lambda o: o.__dict__,
                             sort_keys=True, indent=4)
        return "{" + "\"{}\": {}".format(type_name, payload) + "}"


class DriveData(JSONSerializable):
    """ Simple dataclass to represent the car's drive data """

    def __init__(self,
                 time: int = 0,
                 throttle: int = 0,
                 steering: int = 0,
                 velocity: int = 0,
                 driven_distance: float = 0,
                 obsticle_distance: int = 0,
                 lateral_position: int = 0,
                 angle: float = 0):
        self.time = time
        self.throttle = throttle
        self.steering = steering
        self.velocity = velocity
        self.driven_distance = driven_distance
        self.obsticle_distance = obsticle_distance
        self.lateral_position = lateral_position
        self.angle = angle

    def from_json(json_str: str):
        """ Returns instance from json string """
        dict = json.loads(json_str)
        return DriveData(dict["time"], dict["throttle"],
                         dict["steering"], dict["velocity"],
                         dict["driven_distance"], dict["obsticle_distance"],
                         dict["lateral_position"], dict["angle"])

    def to_json(self) -> str:
        return super().to_json("DriveData")


class ManualDriveInstruction(JSONSerializable):
    """ Simple dataclass to represent a drive instruction for the car """

    def __init__(self, throttle: int = 0, steering: int = 0):
        self.throttle = throttle
        self.steering = steering

    def from_json(json_str: str):
        """ Returns instance from json string """
        dict = json.loads(json_str)
        return ManualDriveInstruction(dict["throttle"], dict["steering"])

    def to_json(self) -> str:
        return super().to_json("ManualDriveInstruction")


class Direction:
    """ Available directions the car can drive in the autonomous modes"""
    LEFT = 0
    FWRD = 1
    RIGHT = 2


class SemiDriveInstruction(JSONSerializable):
    """ Simple dataclass to represent a semi-autonomous drive instruction for the car """

    def __init__(self, direction: Direction = Direction.FWRD):
        self.direction = direction
        self.id = str(uuid4())  # Assign unique id to instruction

    def from_json(json_str: str):
        """ Returns instance from json string """
        dict = json.loads(json_str)
        return SemiDriveInstruction(dict["direction"], dict["id"])

    def to_json(self) -> str:
        return super().to_json("SemiDriveInstruction")


class ParameterConfiguration(JSONSerializable):
    """ Simple dataclass to represent a parameter configuration for the car """

    def __init__(self, steering_kp: int = 0, steering_kd: int = 0, speed_kp: int = 0):
        self.steering_kp = steering_kp
        self.steering_kd = steering_kd
        self.speed_kp = speed_kp

    def from_json(json_str: str):
        """ Returns instance from json string """
        dict = json.loads(json_str)
        return ParameterConfiguration(dict["steering_kp"], dict["steering_kd"], dict["speed_kp"])

    def to_json(self) -> str:
        return super().to_json("ParameterConfiguration")


class MapData:
    """ A graph representation of a map """

    def __init__(self, map: dict = {}):
        self.map = map

    def add_node(self, node: str):
        """ Adds a node to the map """
        if node in self.map:
            print("Map already contains \"{}\"".format(node))
            return

        self.map[node] = []

    def connect_node(self, node_1: str, node_2: str, weight: int):
        """ Connects node_1 to node_2 with weight. Adds nodes if not already in map. """
        if node_1 not in self.map:
            self.add_node(node_1)

        if node_2 not in self.map:
            self.add_node(node_2)

        self.map[node_1].append({node_2: weight})

    def to_json(self) -> str:
        """ Creates a JSON-object of a map, with the type as top level key """
        return "{" + "\"{}\": {}".format("MapData", json.dumps(self.map)) + "}"


def get_type_and_data(json_str):
    """ Returns the data type and json payload """
    try:
        json_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(e.msg)
        return "Error", {}
    data_type = next(iter(json_dict))  # Returns name of first key

    return data_type, json_dict[data_type]
