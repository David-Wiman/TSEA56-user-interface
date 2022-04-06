import json


class JSONSerializable:
    """Enables a simple dataclass to be serialized with JSON"""

    def to_json(self, type_name: str) -> str:
        """Creates a JSON-object from instance, with the type as top level key"""
        payload = json.dumps(self, default=lambda o: o.__dict__,
                             sort_keys=True, indent=4)
        return "\"{}\": {}".format(type_name, payload)


class CarData(JSONSerializable):
    """Simple dataclass to represent the car's status data"""

    time: int
    throttle: float
    steering: float
    driven_distance: float
    obsticle_distance: int
    lateral_position: int
    angle: float

    def __init__(self,
                 time: int = 0,
                 throttle: float = 0,
                 steering: float = 0,
                 driven_distance: float = 0,
                 obsticle_distance: int = 0,
                 lateral_position: int = 0,
                 angle: float = 0):
        self.time = time
        self.throttle = throttle
        self.steering = steering
        self.driven_distance = driven_distance
        self.obsticle_distance = obsticle_distance
        self.lateral_position = lateral_position
        self.angle = angle

    def from_json(json_str: str):
        dict = json.loads(json_str)
        return CarData(dict['time'], dict['throttle'],
                       dict['steering'], dict['driven_distance'],
                       dict['obsticle_distance'], dict['obsticle_distance'],
                       dict['lateral_position'], dict['angle'])


class DriveInstruction(JSONSerializable):
    """Simple dataclass to represent a drive instruction for the car"""

    throttle: float
    steering: float

    def __init__(self, throttle: float = 0, steering: float = 0):
        self.throttle = throttle
        self.steering = steering

    def from_json(json_str: str):
        dict = json.loads(json_str)
        return DriveInstruction(dict['throttle'], dict['steering'])


class ParameterConfiguration(JSONSerializable):
    """Simple dataclass to represent a parameter configuration for the car"""
    temp: int

    def __init__(self, temp: int = 0):
        self.temp = temp

    def from_json(json_str: str):
        dict = json.loads(json_str)
        return ParameterConfiguration(dict['temp'])


def get_type_and_data(json_str):
    """Returns the data type and json payload"""
    try:
        json_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(e.msg)
        return "Error", {}
    data_type = next(iter(json_dict))  # Returns name of first key

    return data_type, json_dict[data_type]
