from enum import Enum

from Python.utils.constant import ABBREV_PRIVACY_D


class AppTypeEnum(Enum):
    SMARTTHINGS = "SmartThings"
    IFTTT = "IFTTT"
    OPENHAB = "OpenHAB"

    def __repr__(self):
        return self.value

    def __str__(self):
        return repr(self)


class MethodTypeEnum(Enum):
    SUBSCRIBE = 0
    SCHEDULE = 1
    RUN = 2
    ACTUATOR = 3
    SINK_MSG = 4
    SINK_HTTP = 5
    SINK_API = 6
    OTHERS = 7


class TcaEnum(Enum):
    TRIGGER = 0
    CONDITION = 1
    ACTUATOR = 2
    SINK_MSG = 3
    SINK_HTTP = 4
    SINK_API = 5

    def __eq__(self, other) -> bool:
        return self.value == other.value

    def __lt__(self, other) -> bool:
        return self.value < other.value

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __hash__(self) -> int:
        return hash(self.value)


class ConnEnum(Enum):
    MATCH = "Match"
    INFLUENCE = "Influence"

    def __repr__(self):
        return self.value

    def __str__(self):
        return repr(self)


class ChainEnum(Enum):
    ACTIVATE = "Activate"
    ENABLE = "Enable"

    def __repr__(self):
        return self.value

    def __str__(self):
        return repr(self)


class PrivacyTypeEnum(Enum):
    IDENTIFICATION = "A"
    LOCALIZATION = "B"
    ACTIVITY = "C1"
    HEALTH = "C2"
    LIFECYCLE = "D"

    def __repr__(self):
        return self.value

    def __str__(self):
        return ABBREV_PRIVACY_D[self.value]


class ThreatTypeEnum(Enum):
    DIRECT = "Single Sink, Direct Exposure"
    IMPLICIT = "Single Sink, Implicit Inference"
    MULTIPLE = "Multiple Sinks, Implicit Inference"

    def __repr__(self):
        return self.value

    def __str__(self):
        return repr(self)
