import json
from uuid import uuid4

from config import DEFAULT_MAP_PATH


class JSONSerializable:
    """ Enables a simple dataclass to be serialized with JSON """

    def to_json(self, type_name: str) -> str:
        """ Creates a JSON-object from instance, with the type as top level key """
        payload = json.dumps(self, default=lambda o: o.__dict__,
                             sort_keys=True, indent=1)

        # \n reserved for end of message char in socket communication
        payload = payload.replace("\n", "")
        return "{" + "\"{}\": {}".format(type_name, payload) + "}"


class DriveData(JSONSerializable):
    """ Simple dataclass to represent the car's drive data """

    def __init__(self,
                 elapsed_time: int = 0,
                 throttle: int = 0,
                 steering: int = 0,
                 speed: int = 0,
                 driving_distance: int = 0,
                 obstacle_distance: int = 0,
                 lateral_position: int = 0,
                 angle: int = 0):
        self.elapsed_time = elapsed_time
        self.throttle = throttle
        self.steering = steering
        self.speed = speed
        self.driving_distance = driving_distance
        self.obstacle_distance = obstacle_distance
        self.lateral_position = lateral_position
        self.angle = angle

    def from_json(json: dict):
        """ Returns instance from json """
        return DriveData(json["elapsed_time"], json["throttle"],
                         json["steering"], json["speed"],
                         json["driving_distance"], json["obstacle_distance"],
                         json["lateral_position"], json["angle"])

    def to_json(self) -> str:
        return super().to_json("DriveData")


class ManualDriveInstruction(JSONSerializable):
    """ Simple dataclass to represent a drive instruction for the car """

    def __init__(self, throttle: int = 0, steering: int = 0):
        self.throttle = throttle
        self.steering = steering

    def from_json(json: dict):
        """ Returns instance from json """
        return ManualDriveInstruction(json["throttle"], json["steering"])

    def to_json(self) -> str:
        return super().to_json("ManualDriveInstruction")


class Direction:
    """ Available directions the car can drive in the autonomous modes """
    LEFT = 0
    FWRD = 1
    RIGHT = 2


class SemiDriveInstruction(JSONSerializable):
    """ Simple dataclass to represent a semi-autonomous drive instruction for the car """

    def __init__(self, direction: Direction = Direction.FWRD):
        self.direction = direction
        self.id = str(uuid4())  # Assign unique id to instruction

    def from_json(json: dict):
        """ Returns instance from json """
        return SemiDriveInstruction(json["direction"], json["id"])

    def to_json(self) -> str:
        return super().to_json("SemiDriveInstruction")


class ParameterConfiguration(JSONSerializable):
    """ Simple dataclass to represent a parameter configuration for the car """

    def __init__(self, steering_kp=0, steering_kd=0, speed_kp=0,
                 speed_ki=0, turn_kd=0, angle_offset=0):
        self.steering_kp = steering_kp
        self.steering_kd = steering_kd
        self.speed_kp = speed_kp
        self.speed_ki = speed_ki
        self.turn_kd = turn_kd
        self.angle_offset = angle_offset

    def from_json(json: dict):
        """ Returns instance from json """
        return ParameterConfiguration(json["steering_kp"], json["steering_kd"],
                                      json["speed_kp"], json["speed_ki"],
                                      json["turn_kd"], json["angle_offset"])

    def to_json(self) -> str:
        return super().to_json("ParameterConfiguration")


class MapData:
    """ A graph representation of a map """

    def __init__(self, map: dict = {}):
        self.map = map

    def add_node(self, node: str):
        """ Adds a unconnected node to the map """
        if node in self.map:
            print("Map already contains \"{}\"".format(node))
            return

        self.map[node] = []

    def connect_node(self, node_1: str, node_2: str, weight: int, is_left=True):
        """ Connects node_1 to node_2 with weight. Adds nodes if not already in map. """
        if node_1 not in self.map:
            self.add_node(node_1)

        if node_2 not in self.map:
            self.add_node(node_2)

        index = 0 if is_left else 1
        edge = {node_2: weight}
        if edge not in self.map[node_1]:
            print("Connecting " + node_1 + " -> " + node_2)
            self.map[node_1].insert(index, edge)

    def verify_complete_map(self):
        """ Returns 'True' if if map is complete """
        is_complete = True  # Assume complete

        # Check each node in map is valid
        for key in self.map.keys():
            # Check if any orphaned nodes
            if len(self.map[key]) == 0:
                print("ERROR: Orphaned node: \"{}\"".format(key))
                is_complete = False

            # Check if too many connecting nodes
            if len(self.map[key]) > 2:
                print("ERROR: Too many connecting nodes for \"{}\": {}".format(
                    key, self.map[key]))
                is_complete = False

        return is_complete

    def load_from_file(self, path: str = DEFAULT_MAP_PATH):
        """ Load a JSON-object map from file at path """
        json_str = ""
        with open(path, "r") as file:
            json_str = " ".join(file.readlines())
        return self.from_json(json_str)

    def save_to_file(self, path: str = DEFAULT_MAP_PATH):
        """ Save map as JSON-object to path """
        with open(path, "w") as file:
            file.write(self.to_json())

    def from_json(self, j_str: str):
        """ Load map from a JSON string """
        return MapData(json.loads(j_str)["MapData"])

    def to_json(self) -> str:
        """ Creates a JSON-object of a map, with MapData as top level key """
        payload = json.dumps(self.map)

        # \n reserved for end of message char in socket communication
        payload = payload.replace("\n", "")
        return "{" + "\"{}\": {}".format("MapData", payload) + "}"


def get_type_and_data(json_str):
    """ Returns the data type and json data """
    try:
        json_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(e.msg)
        return "Error", {}
    data_type = next(iter(json_data))  # Returns name of first key

    return data_type, json_data[data_type]
